from flask import Blueprint, flash, redirect, render_template, request, url_for

from clinic.controllers.helpers import require_role
from clinic.repositories import ClinicRepository
from clinic.services import PatientFlowService

patient_flow_bp = Blueprint("patient_flow", __name__, url_prefix="/patient-flow")


@patient_flow_bp.route("/")
@require_role("secretary", "doctor")
def index():
    flow_items = ClinicRepository().list_patient_flow(today_only=True)
    return render_template("patient_flow/index.html", flow_items=flow_items)


@patient_flow_bp.route("/<int:flow_id>/status", methods=["POST"])
@require_role("secretary", "doctor")
def update_status(flow_id):
    _, errors = PatientFlowService().update_status(flow_id, request.form["next_status"])
    if errors:
        flash(errors[0], "error")
    else:
        flash("Patient status updated.", "success")
    return redirect(url_for("patient_flow.index"))
