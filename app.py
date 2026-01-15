from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import os
import traceback

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

UPLOAD_FOLDER = "uploads"
STATIC_FOLDER = "static"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(STATIC_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        error_msg = ""
        try:
            print("DEBUG: Processing started")
            file = request.files.get("file")
            
            if not file or file.filename == "":
                return render_template("index.html", error="No file selected")

            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            print("DEBUG: File saved")

            df = pd.read_csv(filepath)

            required = {"Date", "Product", "Sales"}
            if not required.issubset(df.columns):
                return render_template("index.html", error="Need Date, Product, Sales columns")

            df["Date"] = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
            df["Sales"] = df["Sales"].astype(str).str.replace(",", "").astype(float)

            df = df.dropna(subset=["Date", "Sales"])

            if df.empty:
                return render_template("index.html", error="No valid data")

            df["Month"] = df["Date"].dt.strftime("%B")
            monthly_sales = df.groupby("Month")["Sales"].sum()
            product_sales = df.groupby("Product")["Sales"].sum()

            print("DEBUG: Best product:", product_sales.idxmax())
            print("DEBUG: Best month:", monthly_sales.idxmax())

            for img in ["static/monthly.png", "static/product.png"]:
                if os.path.exists(img):
                    os.remove(img)

            plt.figure(figsize=(10, 6))
            monthly_sales.sort_index().plot(marker="o")
            plt.title("Monthly Sales")
            plt.savefig("static/monthly.png")
            plt.close()

            plt.figure(figsize=(10, 6))
            product_sales.plot(kind="bar")
            plt.title("Product Sales")
            plt.savefig("static/product.png")
            plt.close()

            print("DEBUG: Plots saved")

            return render_template(
                "index.html",
                best_product=product_sales.idxmax(),
                best_month=monthly_sales.idxmax(),
                total_sales=int(df["Sales"].sum()),
                show_result=True
            )
            
        except Exception as e:
            print("ERROR:", str(e))
            return render_template("index.html", error="Error: " + str(e))

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)