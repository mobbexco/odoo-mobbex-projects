odoo.define("payment_stripe.payment_form", function (require) {
  "use strict";

  var ajax = require("web.ajax");
  var core = require("web.core");
  var Dialog = require("web.Dialog");
  var PaymentForm = require("payment.payment_form");

  var qweb = core.qweb;
  var _t = core._t;

  // ajax.loadXML('/payment_stripe/static/src/xml/stripe_templates.xml', qweb);

  PaymentForm.include({
    // willStart: function () {
    //     return this._super.apply(this, arguments).then(function () {
    //         return ajax.loadJS("https://js.stripe.com/v3/");
    //     })
    // },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * called when clicking on pay now or add payment event to create token for credit card/debit card.
     *
     * @private
     * @param {Event} ev
     * @param {DOMElement} checkedRadio
     * @param {Boolean} addPmEvent
     */
    _createMobbex: function (ev) {
      ev.preventDefault();
      var form = this.el;
    //   console.log(form);
      var checked_radio = this.$('input[type="radio"]:checked');
      var self = this;
      if (ev.type === "submit") {
        var button = $(ev.target).find('*[type="submit"]')[0];
      } else {
        var button = ev.target;
      }

      // first we check that the user has selected a payment method
      if (checked_radio.length === 1) {
        checked_radio = checked_radio[0];

        // we retrieve all the input inside the acquirer form and 'serialize' them to an indexed array
        var acquirer_id = this.getAcquirerIdFromRadio(checked_radio);

        // Get additional values
        var form_dni_mobbex = this.$("input[name=dni_mobbex]").val();
        // console.log(form_dni_mobbex);

        // console.log("acquirer_id", acquirer_id);
        var acquirer_form = false;
        if (this.isNewPaymentRadio(checked_radio)) {
          acquirer_form = this.$("#o_payment_add_token_acq_" + acquirer_id);
        } else {
          acquirer_form = this.$("#o_payment_form_acq_" + acquirer_id);
        }

        // console.log("acquirer_form", acquirer_form);
        var inputs_form = $("input", acquirer_form);
        var ds = $('input[name="data_set"]', acquirer_form)[0];

        // console.log("inputs_form", inputs_form);
        // console.log("ds", ds);

        // if the user is adding a new payment
        if (this.isNewPaymentRadio(checked_radio)) {
          if (this.options.partnerId === undefined) {
            console.warn(
              "payment_form: unset partner_id when adding new token; things could go wrong"
            );
          }
          var form_data = this.getFormData(inputs_form);
        //   console.log(form_data);
          var wrong_input = false;

          inputs_form.toArray().forEach(function (element) {
            //skip the check of non visible inputs
            if ($(element).attr("type") == "hidden") {
              return true;
            }
            $(element)
              .closest("div.form-group")
              .removeClass("o_has_error")
              .find(".form-control, .custom-select")
              .removeClass("is-invalid");
            $(element).siblings(".o_invalid_field").remove();
            //force check of forms validity (useful for Firefox that refill forms automatically on f5)
            $(element).trigger("focusout");
            if (element.dataset.isRequired && element.value.length === 0) {
              $(element)
                .closest("div.form-group")
                .addClass("o_has_error")
                .find(".form-control, .custom-select")
                .addClass("is-invalid");
              $(element)
                .closest("div.form-group")
                .append(
                  '<div style="color: red" class="o_invalid_field" aria-invalid="true">' +
                    _.str.escapeHTML("The value is invalid.") +
                    "</div>"
                );
              wrong_input = true;
            } else if (
              $(element).closest("div.form-group").hasClass("o_has_error")
            ) {
              wrong_input = true;
              $(element)
                .closest("div.form-group")
                .append(
                  '<div style="color: red" class="o_invalid_field" aria-invalid="true">' +
                    _.str.escapeHTML("The value is invalid.") +
                    "</div>"
                );
            }
          });

          if (wrong_input) {
            return;
          }

          this.disableButton(button);
          // do the call to the route stored in the 'data_set' input of the acquirer form, the data must be called 'create-route'
          return this._rpc({
            route: ds.dataset.createRoute,
            params: form_data,
          })
            .then(function (data) {
              // if the server has returned true
              if (data.result) {
                // and it need a 3DS authentication
                if (data["3d_secure"] !== false) {
                  // then we display the 3DS page to the user
                  $("body").html(data["3d_secure"]);
                } else {
                  checked_radio.value = data.id; // set the radio value to the new card id
                  form.submit();
                  return new Promise(function () {});
                }
              }
              // if the server has returned false, we display an error
              else {
                if (data.error) {
                  self.displayError("", data.error);
                } else {
                  // if the server doesn't provide an error message
                  self.displayError(
                    _t("Server Error"),
                    _t(
                      "e.g. Your credit card details are wrong. Please verify."
                    )
                  );
                }
              }
              // here we remove the 'processing' icon from the 'add a new payment' button
              self.enableButton(button);
            })
            .guardedCatch(function (error) {
              error.event.preventDefault();
              // if the rpc fails, pretty obvious
              self.enableButton(button);

              self.displayError(
                _t("Server Error"),
                _t(
                  "We are not able to add your payment method at the moment."
                ) + self._parseError(error)
              );
            });
        }
        // if the user is going to pay with a form payment, then
        else if (this.isFormPaymentRadio(checked_radio)) {
          this.disableButton(button);
          var $tx_url = this.$el.find('input[name="prepare_tx_url"]');
          // if there's a prepare tx url set
          if ($tx_url.length === 1) {
            // if the user wants to save his credit card info
            var form_save_token = acquirer_form
              .find('input[name="o_payment_form_save_token"]')
              .prop("checked");
            // then we call the route to prepare the transaction
            return this._rpc({
              route: $tx_url[0].value,
              params: {
                acquirer_id: parseInt(acquirer_id),
                save_token: form_save_token,
                access_token: self.options.accessToken,
                success_url: self.options.successUrl,
                error_url: self.options.errorUrl,
                callback_method: self.options.callbackMethod,
                order_id: self.options.orderId,
              },
            })
              .then(function (result) {
                // console.log(result);
                if (result) {
                //   console.log(typeof result);
                  // if the server sent us the html form, we create a form element
                  var newForm = document.createElement("form");
                  newForm.setAttribute("method", "post"); // set it to post
                  newForm.setAttribute(
                    "provider",
                    checked_radio.dataset.provider
                  );
                  newForm.hidden = true; // hide it
                //   console.log(result);
                  newForm.innerHTML = result; // put the html sent by the server inside the form
                  // Workaround put value to additional mobbex data
                  if (newForm.elements.form_dni_mobbex)
                    newForm.elements.form_dni_mobbex.value = form_dni_mobbex;
                  var action_url = $(newForm)
                    .find('input[name="data_set"]')
                    .data("actionUrl");
                //   console.log("action_url", action_url);
                //   console.log("newForm", newForm);
                  newForm.setAttribute("action", action_url); // set the action url
                  $(document.getElementsByTagName("body")[0]).append(newForm); // append the form to the body
                  $(newForm).find("input[data-remove-me]").remove(); // remove all the input that should be removed
                  if (action_url) {
                    newForm.submit(); // and finally submit the form
                    return new Promise(function () {});
                  }
                } else {
                  self.displayError(
                    _t("Server Error"),
                    _t("We are not able to redirect you to the payment form.")
                  );
                  self.enableButton(button);
                }
              })
              .guardedCatch(function (error) {
                error.event.preventDefault();
                self.displayError(
                  _t("Server Error"),
                  _t("We are not able to redirect you to the payment form.") +
                    " " +
                    self._parseError(error)
                );
              });
          } else {
            // we append the form to the body and send it.
            this.displayError(
              _t("Cannot setup the payment"),
              _t("We're unable to process your payment.")
            );
            self.enableButton(button);
          }
        } else {
          // if the user is using an old payment then we just submit the form
          this.disableButton(button);
          form.submit();
          return new Promise(function () {});
        }
      } else {
        this.displayError(
          _t("No payment method selected"),
          _t("Please select a payment method.")
        );
        this.enableButton(button);
      }
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    payEvent: function (ev) {
      ev.preventDefault();
      var $checkedRadio = this.$('input[type="radio"]:checked');
      //   console.log($checkedRadio);
      //   console.log($checkedRadio.data("provider"));
      //   console.log(this.isNewPaymentRadio($checkedRadio));
      //   console.log($checkedRadio.length);

      // first we check that the user has selected a mobbex payment method
      if (
        $checkedRadio.length === 1 &&
        $checkedRadio.data("provider") === "mobbex"
      ) {
        // console.log("es mobbex");
        return this._createMobbex(ev);
      } else {
        // console.log("no es mobbex");
        return this._super.apply(this, arguments);
      }
    },
    /**
     * @override
     */
    // addPmEvent: function (ev) {
    //     ev.stopPropagation();
    //     ev.preventDefault();
    //     var $checkedRadio = this.$('input[type="radio"]:checked');

    //     // first we check that the user has selected a stripe as add payment method
    //     if ($checkedRadio.length === 1 && this.isNewPaymentRadio($checkedRadio) && $checkedRadio.data('provider') === 'stripe') {
    //         return this._createStripeToken(ev, $checkedRadio, true);
    //     } else {
    //         return this._super.apply(this, arguments);
    //     }
    // },
  });
});
