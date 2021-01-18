odoo.define("sh_global_search.GlobalSearch", function (require) {
    "use strict";

    var core = require("web.core");
    var Dialog = require("web.Dialog");
    var Widget = require("web.Widget");
    var rpc = require("web.rpc");
    var SystrayMenu = require("web.SystrayMenu");

    var session = require("web.session");
    var _t = core._t;
    var QWeb = core.qweb;
    var show_company = false;
    session.user_has_group("base.group_multi_company").then(function (has_group) {
        show_company = has_group;
    });

    var GlobalSearch = Widget.extend({
        template: "GlobalSearch",
        events: {
            "keydown .sh_search_input input": "_onSearchResultsNavigate",
        },
        init: function () {
            this._search_def = $.Deferred();
            this._super.apply(this, arguments);
            this.show_company = show_company;
        },

        _linkInfo: function (key) {
            var original = this._searchableMenus[key];
            return original;
        },
        _getFieldInfo: function (key) {
            key = key.split("|")[1];
            return key;
        },
        _getcompanyInfo: function (key) {
            key = key.split("|")[0];
            return key;
        },
        _checkIsMenu: function (key) {
            key = key.split("|")[0];
            if (key == "menu") {
                return true;
            } else {
                return false;
            }
        },

        _searchData: function () {
            var query = this.$(".sh_search_input input").val();
            if (query === "") {
                this.$(".sh_search_container").removeClass("has-results");
                this.$(".sh_search_results").empty();
                return;
            }
            var self = this;

            this._rpc({
                model: "global.search",
                method: "get_search_result",
                args: [[query]],
            }).then(function (data) {
                if (data) {
                    self._searchableMenus = data;

                    var results = fuzzy.filter(query, _.keys(self._searchableMenus), {});

                    var results = _.keys(self._searchableMenus);
                    self.$(".sh_search_results").toggleClass("has-results", Boolean(results.length));
                    self.$(".sh_search_results").html(
                        QWeb.render("sh_global_search.MenuSearchResults", {
                            results: results,
                            widget: self,
                        })
                    );
                }
            });
        },
        _onSearchResultsNavigate: function (event) {
            this._search_def.reject();
            this._search_def = $.Deferred();
            setTimeout(this._search_def.resolve.bind(this._search_def), 50);
            this._search_def.done(this._searchData.bind(this));
            return;
        },
    });

    GlobalSearch.prototype.sequence = 4;
    SystrayMenu.Items.push(GlobalSearch);

    return {
        GlobalSearch: GlobalSearch,
    };
});
