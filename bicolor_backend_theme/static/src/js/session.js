odoo.define('multi_company_email.Session', function (require) {
    "use strict";

    var session = require('web.session');
    var SwitchCompanyMenu = require('web.SwitchCompanyMenu');

    SwitchCompanyMenu.include({
        _onSwitchCompanyClick: function (ev) {
            var dropdownItem = $(ev.currentTarget).parent();
            var companyID = dropdownItem.data('company-id');
            //alert(companyID);
            this._rpc({
                model: 'res.config.settings',
                args: [session.uid, companyID],
                method: 'switch_company',
            });
            this._super.apply(this, arguments);
        },
    });

});
