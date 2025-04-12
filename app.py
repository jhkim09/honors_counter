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

    # 판정 수행
    df["평가대상여부"] = df.apply(evaluate, axis=1)

    # O/X 카운트 추가
    o_count = (df["평가대상여부"] == "O").sum()
    x_count = (df["평가대상여부"] == "X").sum()

    # 총계 행 추가
    count_row = pd.DataFrame([{
        "상태": "총계",
        "O건수": o_count,
        "X건수": x_count
    }])
    df = pd.concat([df, count_row], ignore_index=True)

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

        # 판정 및 파일 저장
        df = pd.read_excel(input_path)
        df_result = evaluate_contracts(df)
        df_result.to_excel(output_path, index=False)

        return send_file(
            path_or_file=output_path,
            as_attachment=True,
            download_name=os.path.basename(output_path),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
