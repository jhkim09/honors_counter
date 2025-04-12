from flask import Flask, request, send_file
import pandas as pd
import tempfile
import os

app = Flask(__name__)

# 계약 평가 함수
def evaluate_contracts(df):
    def evaluate(row):
        if row["상태"] != "정상":
            return "X"

        product_name = str(row["보종"])
        payment_type = str(row["납방"])
        monthly_equiv = row["월납환산"]

        if payment_type == "월납":
            if "무배당 아이사랑 첫보험" in product_name:
                return "O" if monthly_equiv >= 15000 else "X"
            else:
                return "O" if monthly_equiv >= 30000 else "X"

        elif payment_type == "일시납":
            return "O" if monthly_equiv >= 30000 else "X"

        return "X"

    df["평가대상여부"] = df.apply(evaluate, axis=1)
    return df

@app.route("/evaluate", methods=["POST"])
def evaluate():
    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400

    file = request.files["file"]
    if not file.filename.endswith(".xlsx"):
        return {"error": "Only .xlsx files are supported"}, 400

    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, file.filename)
        output_path = os.path.join(tmpdir, "evaluated_" + file.filename)
        file.save(input_path)

        df = pd.read_excel(input_path)
        df_result = evaluate_contracts(df)
        df_result.to_excel(output_path, index=False)

        # 결과 파일을 바이너리로 읽은 뒤 메모리에서 전송하고 즉시 삭제
        with open(output_path, "rb") as f:
            data = f.read()

        return send_file(
            path_or_file=output_path,
            as_attachment=True,
            download_name=os.path.basename(output_path),
            mim
