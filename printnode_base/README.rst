Odoo PrintNode Base module
==========================


Change Log
##########

|

* 1.4
    - Added possibility to define number of copies to be printed in "Print Action Button" menu.

* 1.3.1
    - Added constraints not to allow creation of not valid "Print Action Buttons" and "Methods".
    - On product label printing wizard pre-select printer in case only 1 suitable was found.

* 1.3
    - Added possibility to print product labels while processing Incoming Shipment into your Warehouse.
      Also you can mass print product labels directly from individual product or product list.
    - Show info message on User Preferences in case there are User Rules that can redefine Default user Printer.
    - Added examples to Print Action menu for some typical use cases for Delivery Order and Sales Order printing.

* 1.2.1
    - When direct-printing via Print menu, there is popup message informing user about successful printing.
      Now this message can be disabled via Settings.
    - Fixed issue with wrong Delivery Slip printing, after backorder creation.

* 1.2
    -  Make Printer non-required in "Print action buttons" menu. If not defined, than printer will be selected
       based on user or company printer setting.
    -  Added Support for Odoo Enterprise Barcode Interface. Now it is compatible with "Print action buttons" menu.
    -  "Print action buttons" menu now allows to select filter for records, where reports should be auto-printed.
       E.g. Print Delivery Slip only for Pickings of Type = Delivery Order.

* 1.1
    -  Added Support for automatic/manual printing of Shipping Labels.
       Supporting all Odoo Enterprise included Delivery Carries (FedEx, USPS, UPS, bpost and etc.).
       Also Supporting all custom carrier integration modules that are written according to Odoo Standards.
* 1.0
    - Initial version providing robust integration of Odoo with PrintNode for automatic printing.

|
