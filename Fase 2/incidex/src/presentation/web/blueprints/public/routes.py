from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)

@public_bp.route("/")
def index():
    return render_template("public/index.html", title="Incidex")

@public_bp.route("/features")
def features():
    return render_template("public/features.html", title="Características")

@public_bp.route("/support")
def support():
    return render_template("public/support.html", title="Soporte")
