FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501 8502

CMD ["sh", "-c", "streamlit run app.py --server.port 8501 --server.address 0.0.0.0 & streamlit run public_registration.py --server.port 8502 --server.address 0.0.0.0 & wait"] 