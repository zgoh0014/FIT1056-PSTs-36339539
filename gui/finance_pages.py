# gui/finance_pages.py - The Finance & Payments page (Fragment 5.2).
#
# Replaces the PST4 "Payments (stub)" page. Four sections for the front desk:
#   1. Record New Payment       - take a payment from a student.
#   2. Student Payment History  - every payment one student has made.
#   3. All Payments             - school-wide takings at a glance.
#   4. Export Reports           - save the finance / attendance log as CSV.
#
# As with every gui/ file, this page only collects input and displays results.
# Validation, saving and the CSV writing all happen in ScheduleManager.

import os
import datetime

import pandas as pd
import streamlit as st

# The usual ways a Malaysian music school gets paid. "Other" lets the
# receptionist type something not on the list.
PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card", "Bank Transfer", "E-wallet", "Other"]

# Exported CSVs go in reports/ at the project root (ignored by git).
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

FLASH_KEY = "finance_page_flash"


def show_finance_page(manager):
    """Renders the UI for all financial operations."""
    st.header("Finance & Payments")

    # Success message carried across st.rerun() (same pattern as the student page).
    flash = st.session_state.pop(FLASH_KEY, None)
    if flash:
        st.success(flash)

    if not manager.students:
        st.info("There are no students on file yet. Register a student before recording payments.")
        return

    _show_record_payment_section(manager)
    st.divider()
    _show_history_section(manager)
    st.divider()
    _show_all_payments_section(manager)
    st.divider()
    _show_export_section(manager)


def _student_label(student):
    """How a student appears in a dropdown. The ID is shown so two students
    with the same name can still be told apart."""
    return f"{student.name} (ID {student.id})"


# ----------------------------------------------------------------------
# 1. Record a payment
# ----------------------------------------------------------------------

def _show_record_payment_section(manager):
    st.subheader("Record New Payment")

    # st.form: nothing is sent until "Record Payment" is pressed.
    with st.form("payment_form", clear_on_submit=True):
        # The dropdown holds the StudentUser objects themselves (not a
        # name->id dictionary, which would break on duplicate names).
        student = st.selectbox("Select Student", manager.students, format_func=_student_label)
        col1, col2 = st.columns(2)
        amount = col1.number_input("Payment Amount (RM)", min_value=0.01, value=100.00, step=10.00, format="%.2f")
        method = col2.selectbox("Payment Method", PAYMENT_METHODS)
        other_method = st.text_input("If 'Other', type the method here", placeholder="e.g. Cheque")
        submitted = st.form_submit_button("Record Payment", type="primary")

    if not submitted:
        return

    if method == "Other":
        method = other_method.strip()
        if not method:
            st.warning("You chose 'Other' - please type the payment method.")
            return

    # The manager validates everything again (student exists, amount > 0,
    # method not blank) and returns None if it refuses the payment.
    record = manager.record_payment(student.id, amount, method)
    if record:
        st.session_state[FLASH_KEY] = (
            f"Payment #{record['payment_id']} of RM {record['amount']:.2f} ({record['method']}) "
            f"recorded for {student.name}."
        )
        # Re-run so the history and totals below already include this payment.
        st.rerun()
    else:
        st.error("The payment could not be recorded. Please check the amount and method.")


# ----------------------------------------------------------------------
# 2. One student's history
# ----------------------------------------------------------------------

def _show_history_section(manager):
    st.subheader("View Student Payment History")
    student = st.selectbox(
        "Select Student to View History",
        manager.students,
        format_func=_student_label,
        key="history_student",
    )

    history = manager.get_payment_history(student.id)
    if not history:
        st.info(f"{student.name} has no payment history.")
        return

    col1, col2 = st.columns(2)
    col1.metric("Payments made", len(history))
    col2.metric("Total paid", f"RM {manager.get_total_paid(student.id):,.2f}")

    # Convert the list of dictionaries to a DataFrame and tidy the columns.
    df = pd.DataFrame(history)
    df = df.rename(columns={
        "payment_id": "Payment #",
        "amount": "Amount (RM)",
        "method": "Method",
        "timestamp": "Date & Time",
    }).drop(columns=["student_id"])
    df["Date & Time"] = df["Date & Time"].str.replace("T", " ")
    st.dataframe(df, hide_index=True, column_config={
        "Amount (RM)": st.column_config.NumberColumn(format="%.2f"),
    })


# ----------------------------------------------------------------------
# 3. School-wide takings
# ----------------------------------------------------------------------

def _show_all_payments_section(manager):
    st.subheader("All Payments")
    if not manager.finance_log:
        st.caption("No payments have been recorded yet.")
        return

    rows = []
    for p in reversed(manager.finance_log):  # newest first
        student = manager.find_student_by_id(p.get("student_id"))
        rows.append({
            "Payment #": p.get("payment_id", "-"),
            "Date & Time": str(p.get("timestamp", "")).replace("T", " "),
            # A payment outlives a removed student - show the ID instead of crashing.
            "Student": student.name if student else f"Student #{p.get('student_id')} (removed)",
            "Amount (RM)": p.get("amount", 0),
            "Method": p.get("method", ""),
        })

    today = datetime.date.today().isoformat()
    total = sum(r["Amount (RM)"] for r in rows)
    today_total = sum(p.get("amount", 0) for p in manager.finance_log
                      if str(p.get("timestamp", ""))[:10] == today)

    col1, col2, col3 = st.columns(3)
    col1.metric("Payments recorded", len(rows))
    col2.metric("Total takings", f"RM {total:,.2f}")
    col3.metric("Taken today", f"RM {today_total:,.2f}")
    st.dataframe(pd.DataFrame(rows), hide_index=True, column_config={
        "Amount (RM)": st.column_config.NumberColumn(format="%.2f"),
    })


# ----------------------------------------------------------------------
# 4. CSV export
# ----------------------------------------------------------------------

def _show_export_section(manager):
    st.subheader("Export Reports")
    st.caption(f"Reports are saved as CSV files in {REPORTS_DIR} and can also be downloaded here.")

    col1, col2 = st.columns(2)
    kind = col1.selectbox("Report type", list(manager.REPORT_KINDS), format_func=str.title)
    col2.write("")  # spacer so the button lines up with the dropdown
    if col2.button("Export to CSV"):
        stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_path = os.path.join(REPORTS_DIR, f"{kind}_report_{stamp}.csv")
        rows = manager.export_report(kind, out_path)
        if rows is None:
            st.error("The report could not be saved. Is the file open in another program?")
        else:
            # Remember the file so the download button survives the next re-run.
            st.session_state["last_export"] = out_path
            st.success(f"Exported {rows} row(s) to {out_path}")

    last = st.session_state.get("last_export")
    if last and os.path.exists(last):
        with open(last, "rb") as f:
            st.download_button("Download " + os.path.basename(last), f.read(),
                               file_name=os.path.basename(last), mime="text/csv")
