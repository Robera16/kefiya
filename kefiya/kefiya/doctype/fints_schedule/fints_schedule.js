// Copyright (c) 2019, jHetzer and contributors
// For license information, please see license.txt

{% include "kefiya/public/js/controllers/fints_interactive.js" %}

frappe.ui.form.on('FinTS Schedule', {
	onload: function(frm) {
		kefiya.interactive.progressbar(frm);
	},
	refresh: function(frm) {
		frm.clear_custom_buttons();
		frm.events.import_transactions(frm);
	},
	import_transactions: function(frm) {
		frm.add_custom_button(__("Import Transaction"), function(){
			frm.save().then(() => {
				frappe.call({
					method: "kefiya.kefiya.doctype.fints_schedule.fints_schedule.scheduled_import_fints_payments",
					args: {
						'manual': true
					}
				});
			});
		}).addClass("btn-primary");
	}
});
