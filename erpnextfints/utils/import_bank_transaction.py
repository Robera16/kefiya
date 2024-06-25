# coding=utf-8
from __future__ import unicode_literals

import hashlib
import frappe
from frappe import _

from erpnextfints.erpnextfints.doctype.kefiya_bank_statement_import.kefiya_bank_statement_import import get_bank_account_data

class ImportBankTransaction:
    def __init__(self, fints_login, interactive, allow_error=False):
        self.allow_error = allow_error
        self.bank_transactions = []
        self.fints_login = fints_login
        self.default_customer = fints_login.default_customer
        self.default_supplier = fints_login.default_supplier
        self.interactive = interactive

    def fints_import(self, fints_transaction):
        # F841 total_items = len(fints_transaction)
        self.interactive.progress = 0
        total_transactions = len(fints_transaction)

        for idx, t in enumerate(fints_transaction):
            # Convert to positive value if required
            amount = abs(float(t['amount']['amount']))
            status = t['status'].lower()

            if amount == 0:
                continue

            if status not in ['c', 'd']:
                frappe.log_error(
                    _('Payment type not handled'),
                    'FinTS Import Error'
                )
                continue

            if status == 'c' and not self.fints_login.enable_received:
                continue

            if status == 'd' and not self.fints_login.enable_pay:
                continue

            txn_number = idx + 1
            progress = txn_number / total_transactions * 100
            message = _('Query transaction {0} of {1}').format(
                txn_number,
                total_transactions
            )
            self.interactive.show_progress_realtime(
                message, progress, reload=False
            )

            # date is in YYYY.MM.DD (json)
            date = t['date']
            applicant_name = t['applicant_name']
            posting_text = t['posting_text']
            purpose = t['purpose']
            applicant_iban = t['applicant_iban']
            applicant_bin = t['applicant_bin']

            remarkType = ''
            paid_to = None
            paid_from = None

            uniquestr = "{0},{1},{2},{3},{4}".format(
                date,
                amount,
                applicant_name,
                posting_text,
                purpose
            )

            transaction_id = hashlib.md5(uniquestr.encode()).hexdigest()
            if frappe.db.exists(
                'Bank Transaction', {
                    'reference_number': transaction_id
                }
            ):
                continue

            if status == 'c':
                payment_type = 'Receive'
                party_type = 'Customer'
                paid_to = self.fints_login.erpnext_account  # noqa: E501
                remarkType = 'Sender'
                deposit = amount
                withdrawal = 0
            elif status == 'd':
                payment_type = 'Pay'
                party_type = 'Supplier'
                paid_from = self.fints_login.erpnext_account  # noqa: E501
                remarkType = 'Receiver'
                deposit = 0
                withdrawal = amount

            party, party_type = get_bank_account_data(applicant_iban)

            default_bank_account = frappe.db.get_value(party_type, party, "default_bank_account")
            bank_party_account_number = ""
            if default_bank_account:
                bank_party_account_number = frappe.db.get_value("Bank Account", default_bank_account, "bank_account_no")

            bank_transaction = frappe.get_doc({
                'doctype': 'Bank Transaction',
                'date': date,
                'status': 'Unreconciled',
                'bank_account': self.fints_login.erpnext_account,
                'company': self.fints_login.company,
                'deposit': deposit,
                'withdrawal': withdrawal,
                'description': purpose,
                'reference_number': transaction_id,
                'allocated_amount': 0,
                'unallocated_amount': amount,
                'party_type': party_type,
                'party': party,
                'bank_party_name': default_bank_account,
                'bank_party_account_number': bank_party_account_number,
                'bank_party_iban': t['applicant_iban'],
                'docstatus': 1
            })
            bank_transaction.insert()
            self.bank_transactions.append(bank_transaction)