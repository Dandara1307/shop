import cv2
from pyzbar.pyzbar import decode
import pandas as pd
from fpdf import FPDF
from tkinter import Tk, Button, Label, messagebox
from datetime import datetime
import os
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

# Criação de diretórios e CSV de registros
os.makedirs("etiquetas", exist_ok=True)
registros_path = "registros.csv"
if not os.path.exists(registros_path):
    df_init = pd.DataFrame(columns=["DataHora", "Nome", "Endereco", "CEP", "OrdemColeta", "ArquivoEtiqueta"])
    df_init.to_csv(registros_path, index=False)

# Função para extrair texto do QR
def extrair_texto_qr(frame):
    for barcode in decode(frame):
        dados = barcode.data.decode("utf-8")
        return dados
    return None

# Função para gerar etiqueta PDF
def gerar_etiqueta(nome, endereco, cep, ordem_coleta):
    agora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    arquivo_pdf = f"etiquetas/{nome.replace(' ', '_')}_{agora}.pdf"

    # Gera código de barras
    barcode_img_path = f"etiquetas/barcode_{ordem_coleta}.png"
    code128 = Code128(ordem_coleta, writer=ImageWriter())
    code128.save(barcode_img_path)

    # Cria o PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Etiqueta de Envio", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Nome: {nome}", ln=True)
    pdf.cell(200, 10, txt=f"Endereço: {endereco}", ln=True)
    pdf.cell(200, 10, txt=f"CEP: {cep}", ln=True)
    pdf.cell(200, 10, txt=f"Ordem de Coleta: {ordem_coleta}", ln=True)
    pdf.cell(200, 10, txt=f"Emitido em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True)

    # Adiciona o código de barras
    pdf.image(barcode_img_path, x=60, y=100, w=90)

    pdf.output(arquivo_pdf)

    # Imprime no Windows
    os.startfile(arquivo_pdf, "print")

    return arquivo_pdf

# Lê QR da câmera e processa
def ler_qr_camera():
    cap = cv2.VideoCapture(0)
    encontrado = False
    dados_extraidos = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        texto = extrair_texto_qr(frame)
        cv2.imshow("Leitor QR - Pressione 'q' para sair", frame)

        if texto:
            dados_extraidos = texto
            encontrado = True
            break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if not encontrado or not dados_extraidos:
        messagebox.showwarning("Aviso", "Nenhum QR code detectado.")
        return

    try:
        print("===== DADOS DO QR LIDOS =====")
        print(dados_extraidos)
        print("=============================")

        linhas = dados_extraidos.split("\n")
        nome = linhas[0].strip() if len(linhas) > 0 else "Destinatário"
        endereco = next((l.strip() for l in linhas if "Rua" in l or "Av" in l), "Endereço não encontrado")
        cep = "00000-000"

        for linha in linhas:
            if "CEP" in linha.upper():
                partes = linha.split(":")
                if len(partes) > 1:
                    cep = partes[1].strip()

        ordem_coleta = None
        for linha in linhas:
            linha_limpa = linha.strip()
            if linha_limpa.isdigit() and linha_limpa.startswith("4") and len(linha_limpa) == 9:
                ordem_coleta = linha_limpa
                break

        if not ordem_coleta:
            raise ValueError("Número da ordem de coleta não encontrado.")

        arq_pdf = gerar_etiqueta(nome, endereco, cep, ordem_coleta)
        registrar(nome, endereco, cep, ordem_coleta, arq_pdf)
        messagebox.showinfo("Sucesso", f"Etiqueta gerada para {nome}")

    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao processar dados:\n{str(e)}")

# Registrar os dados no CSV
def registrar(nome, endereco, cep, ordem_coleta, arquivo_pdf):
    df = pd.read_csv(registros_path)
    novo = {
        "DataHora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Nome": nome,
        "Endereco": endereco,
        "CEP": cep,
        "OrdemColeta": ordem_coleta,
        "ArquivoEtiqueta": arquivo_pdf
    }
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    df.to_csv(registros_path, index=False)

# Interface gráfica
app = Tk()
app.title("Leitor de QR Shopee - Geração de Etiquetas")
app.geometry("400x200")

Label(app, text="Clique no botão abaixo para ler o QR Code").pack(pady=20)
Button(app, text="Ler QR Code", command=ler_qr_camera, height=2, width=20).pack()

app.mainloop()
