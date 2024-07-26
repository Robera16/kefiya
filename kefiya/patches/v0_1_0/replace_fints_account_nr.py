# -*- coding: utf-8 -*-
# Copyright (c) 2019, jHetzer and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe


def execute(): # noqa E103
    doctype = "Kefiya Login"
    frappe.reload_doc("kefiya", "doctype", "fints_login")

    for account in frappe.get_all(doctype):
        if frappe.db.has_column("Kefiya Login", 'account_nr'):
            accountIban = frappe.db.get_value(
                "Kefiya Login",
                {'name': account.name}, 'account_iban')
            accountNr = frappe.db.get_value(
                "Kefiya Login",
                {'name': account.name}, 'account_nr')
            if not accountIban and accountNr:
                doc = frappe.get_doc(doctype, account)
                doc.account_iban = accountNr
                doc.save()
