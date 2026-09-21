"""
app.py
เว็บแอป Streamlit สำหรับโหลดโมเดลที่ฝึกไว้ (.pkl) แล้วให้ผู้ใช้กรอกค่าฟีเจอร์
เพื่อทำนายผล (ตัวอย่างนี้ตั้งชื่อหัวข้อว่า "จำแนกโรค COVID")

หมายเหตุสำคัญ: โค้ดนี้ไม่สามารถเชื่อมต่อไปดึงไฟล์จาก Google Drive ของคุณ
โดยอัตโนมัติ (ไม่มีสิทธิ์เข้าถึงลิงก์ที่แชร์มา) ดังนั้นให้ทำอย่างใดอย่างหนึ่ง:
  1) ดาวน์โหลดโฟลเดอร์ "models" จาก Google Drive มาไว้ในเครื่อง/เซิร์ฟเวอร์
     เดียวกับไฟล์ app.py นี้ (จะสร้างโฟลเดอร์ชื่อ "models" ให้อัตโนมัติถ้ายังไม่มี)
  2) หรือใช้ปุ่มอัปโหลดไฟล์ .pkl ในแอปแทนก็ได้ (มีให้เลือกในแอปนี้)
"""

import os
import glob
import joblib
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------
# 1) ตั้งค่าหน้าเว็บและหัวข้อ
# ---------------------------------------------------------------
st.set_page_config(page_title="จำแนกโรค COVID", page_icon="🩺", layout="centered")
st.title("โปรแกรมจำแนกโรค covid จากภาพ X-ray")

# โฟลเดอร์ที่เก็บไฟล์โมเดล (.pkl) ทั้งหมด - ให้วางไฟล์ที่ดาวน์โหลดจาก
# Google Drive โฟลเดอร์ "models" ไว้ในโฟลเดอร์นี้
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)


# ---------------------------------------------------------------
# 2) ฟังก์ชันโหลดโมเดลด้วย joblib (มี cache กันโหลดซ้ำทุกครั้งที่กดปุ่ม)
# ---------------------------------------------------------------
@st.cache_resource
def load_model(model_path: str):
    """โหลดไฟล์โมเดล .pkl ด้วย joblib"""
    return joblib.load(model_path)


# ---------------------------------------------------------------
# 3) UI สำหรับให้ผู้ใช้เลือกโมเดลเอง
#    - แบบที่ 1: เลือกจากไฟล์ .pkl ที่อยู่ในโฟลเดอร์ models/
#    - แบบที่ 2: อัปโหลดไฟล์ .pkl เอง (เผื่อรันบนเซิร์ฟเวอร์ที่ไม่มีไฟล์อยู่แล้ว)
# ---------------------------------------------------------------
st.sidebar.header("⚙️ เลือกโมเดล")

model_files = sorted(glob.glob(os.path.join(MODEL_DIR, "*.pkl")))
model_source = st.sidebar.radio(
    "แหล่งที่มาของไฟล์โมเดล",
    ["เลือกจากโฟลเดอร์ models/", "อัปโหลดไฟล์ .pkl เอง"],
)

model = None
model_name_display = None

if model_source == "เลือกจากโฟลเดอร์ models/":
    if not model_files:
        st.sidebar.warning(
            "ยังไม่พบไฟล์ .pkl ในโฟลเดอร์ 'models/' "
            "กรุณาดาวน์โหลดไฟล์จาก Google Drive มาวางไว้ในโฟลเดอร์นี้ "
            "หรือเปลี่ยนไปใช้วิธี 'อัปโหลดไฟล์ .pkl เอง' แทน"
        )
    else:
        selected_path = st.sidebar.selectbox("เลือกไฟล์โมเดล", model_files)
        model = load_model(selected_path)
        model_name_display = os.path.basename(selected_path)
else:
    uploaded_model = st.sidebar.file_uploader("อัปโหลดไฟล์โมเดล (.pkl)", type=["pkl"])
    if uploaded_model is not None:
        # บันทึกไฟล์ที่อัปโหลดลงดิสก์ชั่วคราวก่อน แล้วค่อยโหลดด้วย joblib
        temp_path = os.path.join(MODEL_DIR, uploaded_model.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_model.getbuffer())
        model = load_model(temp_path)
        model_name_display = uploaded_model.name

if model_name_display:
    st.sidebar.success(f"โหลดโมเดล '{model_name_display}' สำเร็จแล้ว ✅")


# ---------------------------------------------------------------
# 4) ช่องกรอกค่าฟีเจอร์ (features)
#    *** จุดที่ต้องแก้ไขให้ตรงกับข้อมูลที่ใช้ฝึกโมเดลของคุณจริง ๆ ***
#    ตัวอย่างด้านล่างสมมติว่าฝึกโมเดลจากข้อมูลอาการ/ข้อมูลผู้ป่วยเบื้องต้น
#    เปลี่ยนชื่อคอลัมน์ ประเภทข้อมูล และค่าที่เลือกได้ ให้ตรงกับ dataset จริง
# ---------------------------------------------------------------
st.header("📋 กรอกข้อมูลเพื่อทำนาย")

# ตัวแปรตัวเลข (numeric) -> ใช้ st.number_input
age = st.number_input("อายุ (ปี)", min_value=0, max_value=120, value=30, step=1)
temperature = st.number_input("อุณหภูมิร่างกาย (°C)", min_value=30.0, max_value=45.0, value=36.5, step=0.1)
spo2 = st.number_input("ค่าออกซิเจนในเลือด SpO2 (%)", min_value=0, max_value=100, value=98, step=1)

# ตัวแปรหมวดหมู่ (categorical) -> ใช้ st.selectbox
gender = st.selectbox("เพศ", ["ชาย", "หญิง"])
cough = st.selectbox("มีอาการไอหรือไม่", ["มี", "ไม่มี"])
fever = st.selectbox("มีอาการไข้หรือไม่", ["มี", "ไม่มี"])

# รวมค่าที่กรอกทั้งหมดไว้ในรูปแบบ dict ก่อน แล้วค่อยแปลงเป็น DataFrame
input_dict = {
    "age": [age],
    "temperature": [temperature],
    "spo2": [spo2],
    "gender": [gender],
    "cough": [cough],
    "fever": [fever],
}
input_df = pd.DataFrame(input_dict)

st.write("ข้อมูลที่กรอก:")
st.dataframe(input_df, use_container_width=True)


# ---------------------------------------------------------------
# 5) ฟังก์ชันแปลงข้อมูล (preprocessing) ให้ตรงกับตอนฝึกโมเดล
#    *** สำคัญมาก: ต้องแก้ไขให้ตรงกับขั้นตอนที่ใช้ตอนฝึกโมเดลจริง ***
#    ตัวอย่างนี้ใช้ one-hot encoding ผ่าน pd.get_dummies แล้วจัดคอลัมน์
#    ให้ตรงกับตอน fit โมเดล (เรียงลำดับคอลัมน์ให้เหมือนกันทุกประการ)
# ---------------------------------------------------------------
def preprocess(df: pd.DataFrame, trained_model) -> pd.DataFrame:
    """แปลงข้อมูลดิบจากฟอร์มให้อยู่ในรูปแบบเดียวกับตอนฝึกโมเดล"""

    # one-hot encode คอลัมน์ข้อความ (categorical) เหมือนตอนฝึก
    df_encoded = pd.get_dummies(df, columns=["gender", "cough", "fever"])

    # ถ้าโมเดล (เช่น จาก scikit-learn) มีการบันทึกชื่อคอลัมน์ตอนฝึกไว้
    # (attribute feature_names_in_) ให้ใช้ reindex เพื่อจัดคอลัมน์ให้ตรงกัน
    # เติมคอลัมน์ที่ขาดด้วยค่า 0 และตัดคอลัมน์ที่เกินทิ้ง
    if hasattr(trained_model, "feature_names_in_"):
        df_encoded = df_encoded.reindex(
            columns=trained_model.feature_names_in_, fill_value=0
        )
    else:
        # ถ้าโมเดลไม่มี feature_names_in_ ให้กำหนดรายชื่อคอลัมน์ตอนฝึก
        # ไว้เองตรงนี้ (แก้ไขรายการนี้ให้ตรงกับตอน fit จริง)
        expected_columns = [
            "age", "temperature", "spo2",
            "gender_ชาย", "gender_หญิง",
            "cough_มี", "cough_ไม่มี",
            "fever_มี", "fever_ไม่มี",
        ]
        df_encoded = df_encoded.reindex(columns=expected_columns, fill_value=0)

    return df_encoded


# ---------------------------------------------------------------
# 6) ปุ่มทำนายผล
# ---------------------------------------------------------------
if st.button("ทำนายผล"):
    if model is None:
        st.error("กรุณาเลือกหรืออัปโหลดไฟล์โมเดลก่อนกดทำนายผล")
    else:
        try:
            # แปลงข้อมูลให้ตรงรูปแบบตอนฝึก
            X_input = preprocess(input_df, model)

            # ทำนายผล
            prediction = model.predict(X_input)[0]

            # ถ้าโมเดลรองรับ predict_proba ให้แสดงค่าความมั่นใจด้วย
            proba_text = ""
            if hasattr(model, "predict_proba"):
                proba = model.predict_proba(X_input)[0]
                max_proba = max(proba) * 100
                proba_text = f" (ความมั่นใจประมาณ {max_proba:.2f}%)"

            # แสดงผลลัพธ์ให้อ่านง่าย
            # *** แก้ label ให้ตรงกับค่าที่โมเดลของคุณทำนายออกมาจริง เช่น 0/1 หรือชื่อ class ***
            if str(prediction) in ["1", "positive", "Positive", "COVID", "covid"]:
                st.error(f"ผลการทำนาย: มีความเสี่ยงเป็น COVID{proba_text} ⚠️")
            else:
                st.success(f"ผลการทำนาย: ไม่พบความเสี่ยงเป็น COVID{proba_text} ✅")

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดระหว่างทำนายผล: {e}")
