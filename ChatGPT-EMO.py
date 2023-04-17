# pyinstaller --windowed ChatGPT-EMO.py --onefile  --icon="C:\Users\emo\python\images\openai.ico" 
import requests
import json
import webbrowser
import pyperclip
import time
import os
import openai
import PySimpleGUI as sg
import configparser
import threading
import sys
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode, urlsafe_b64decode
ERROR_MESSAGES = {
    "EMPTY_API_KEY": "Por favor, introduce una clave API.",
}

def check_for_updates():
    url = "https://api.github.com/repos/emo44/ChatGPT-API/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        
        latest_version = data['tag_name']
        current_version = "V1.0.4"  # Define tu versión actual aquí
        if current_version != latest_version:
            sg.popup(
                f"¡Hay una nueva versión disponible ({latest_version})!",
                title="Actualización disponible",
                keep_on_top=True,
                modal=True,
                location=(None, None),
                text_color="red",
                button_color=("white", "blue"),
                custom_text=("Ir a la página de Github", "Cerrar")
            )
            webbrowser.open("https://github.com/emo44/ChatGPT-API")

def generate_encryption_key():
    return Fernet.generate_key()

def encrypt_api_key(api_key, encryption_key):
    fernet = Fernet(encryption_key)
    return fernet.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_api_key, encryption_key):
    fernet = Fernet(encryption_key)
    return fernet.decrypt(encrypted_api_key.encode()).decode()


def generate_response_async(question, window, thread_event):
    try:
        if thread_event.is_set():
            return

        response, response_cost = generate_response(question)

        if not thread_event.is_set():
            window.write_event_value('-RESPONSE-', (response, response_cost))
            window.write_event_value('-LOG-', f"Pregunta: {question}\nRespuesta: {response}\n\n")
    except Exception as e:
        window.write_event_value('-ERROR-', str(e))


def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")

    if "API" in config.sections() and "api_key" in config["API"]:
        encrypted_api_key = config["API"]["api_key"]
        encryption_key = urlsafe_b64decode(config["API"]["encryption_key"])
        api_key = decrypt_api_key(encrypted_api_key, encryption_key)
    else:
        api_key = None

    if "Cost" in config.sections() and "total_cost" in config["Cost"]:
        total_cost = float(config["Cost"]["total_cost"])
    else:
        total_cost = 0.0
    if os.path.isfile('log.txt'):
        a=1
    else:
        file = open("log.txt", "w")
        file.close()


    return api_key, total_cost,config
def save_api_key_to_config(api_key, encryption_key):
    config = configparser.ConfigParser()
    config["API"] = {
        "api_key": encrypt_api_key(api_key, encryption_key),
        "encryption_key": urlsafe_b64encode(encryption_key).decode(),
    }
    if not config.has_section("Cost"):
        config["Cost"] = {"total_cost": "0.0"}

    with open("config.ini", "w") as configfile:
        config.write(configfile)

api_key, total_cost, config = load_config()


if api_key is None:
    layout = [
        [sg.Text("Por favor, introduce tu API key, la cifraré por seguridad:")],
        [sg.InputText("", key="input_api_key")],
        [sg.Button("OK", key="submit_api_key"), sg.Button("Cancelar", key="cancel_api_key")],
    ]
    window = sg.Window("Introduce tu API key", layout, keep_on_top=True)

    while True:
        event, values = window.read()

        if event == "submit_api_key":
            api_key = values["input_api_key"]
            if not api_key:
                window["api_key_error"].update(ERROR_MESSAGES["EMPTY_API_KEY"])
            else:
                encryption_key = generate_encryption_key()
                save_api_key_to_config(api_key, encryption_key)
                window.close()
                break
        elif event == "cancel_api_key" or event == sg.WIN_CLOSED:
            sys.exit()


def save_total_cost(total_cost, config):
    config = configparser.ConfigParser()
    config.read("config.ini")

    if not config.has_section("Cost"):
        config.add_section("Cost")

    config.set("Cost", "total_cost", str(total_cost))

    with open("config.ini", "w") as configfile:
        config.write(configfile)


api_key, total_cost, config = load_config()



if api_key is None:
    layout = [
        [sg.Text("No se encontró el archivo config.ini o el valor de la API. Por favor, introduce tu API key:")],
        [sg.InputText("", key="input_api_key")],
        [sg.Button("OK", key="submit_api_key"), sg.Button("Cancelar", key="cancel_api_key")],
    ]
    window = sg.Window("Introduce tu API key", layout, keep_on_top=True)
    
    while True:
        event, values = window.read()
        if event == "submit_api_key":
            api_key = values["input_api_key"]
            encryption_key = generate_encryption_key()
            encrypted_api_key = encrypt_api_key(api_key, encryption_key)
            config = configparser.ConfigParser()
            config["API"] = {
                "api_key": encrypted_api_key,
                "encryption_key": urlsafe_b64encode(encryption_key).decode(),
            }
            with open("config.ini", "w") as configfile:
                config.write(configfile)
            window.close()
            break
        elif event == "cancel_api_key" or event == sg.WIN_CLOSED:
            sys.exit()


openai.api_key = api_key

def show_about_window():
    layout = [[sg.Text("Creado por Emo para el modelo ChatGPT 3.5 Turbo,\ngratis la api hasta el 1 de mayo del 2023 con 18$ de regalo")], [sg.Button("Cerrar")]]
    window = sg.Window("Acerca de", layout, keep_on_top=True)
    while True:
        event, values = window.read()
        if event == "Cerrar" or event == sg.WIN_CLOSED:
            break
    window.close()
def show_configuration_window():
    layout = [
        [sg.Text("Introduzca la nueva clave API:")],
        [sg.InputText("", key="new_api_key")],
        [sg.Text("", key="new_api_key_error", text_color="red")],
        [sg.Button("Guardar", key="save_api_key"), sg.Button("Cancelar", key="cancel_new_api_key")],  # Cambia aquí
    ]
    window = sg.Window("Configuración", layout, keep_on_top=True)

    while True:
        event, values = window.read()
        if event == "save_api_key":  # Cambia aquí
            new_api_key = values["new_api_key"]
            if not new_api_key:
                window["new_api_key_error"].update(ERROR_MESSAGES["EMPTY_API_KEY"])
            else:
                update_api_key(new_api_key)
                window.close()
                sg.popup("La clave API ha sido actualizada.")
                break
        elif event == "cancel_new_api_key" or event == sg.WIN_CLOSED:
            break

    window.close()

def update_api_key(new_api_key):
    global api_key, config
    encryption_key = generate_encryption_key()
    save_api_key_to_config(new_api_key, encryption_key)
    api_key = new_api_key
    config = configparser.ConfigParser()
    config.read("config.ini")
    openai.api_key = api_key  # Agrega esta línea para actualizar la clave API en la biblioteca OpenAI
   


message_history = [{"role": "system", "content": "You are a helpful assistant."}]
def main():
    
    global total_cost
    api_key, total_cost, config = load_config()
    save_total_cost(total_cost, config)



    # Define the layout of the GUI


    layout = [
        [sg.Text("Pregunta:  "), sg.Multiline(size=(100, 10), key="question", text_color='red')],
 
       
        [sg.Text("", expand_x=True), sg.Button("Enviar", size=(10, 1), key="submit", button_color=("white", "green")), sg.Button("Cancelar", size=(10, 1), key="cancel"), sg.Button("Borrar", size=(10, 1), key="clear_question")],
        [sg.Text("Respuesta:"), sg.Multiline(size=(100, 10), key="response", text_color='blue')],

        

        [sg.Text("", expand_x=True), sg.Button("Borrar", size=(10, 1), key="clear_response"), sg.Button("Copiar", size=(10, 1), key="copy_response")],
        [sg.Text("Log:           "),sg.Multiline(size=(100, 10), key="log_output")],
        [sg.Text("", expand_x=True),sg.Button("Borrar log", size=(10, 1), key="clear_log")],
        [sg.Text("Costo total: $", size=(15, 1)), sg.Text(f"{total_cost:.2f}", key="total_cost_value", size=(10, 1))],
        [sg.Button("Configuración", size=(14, 1), key="config"), sg.Button("Acerca", size=(10, 1), key="about"), sg.Button("Salir", size=(10, 1), key="exit", button_color=("white", "red"), pad=((500, 0), (10, 10)))]

    ]
    


    # Create the window
    window = sg.Window("Emo Openai API interface", layout, size=(800, 700))
    check_for_updates()
    while True:
        event, values = window.read()
#         with open("log.txt", "r") as f:
#             log_contents = f.read()
#             window["log_output"].update(log_contents)

        if event in (None, "exit"):
            break


        if event == "submit":
            # Desactivar el botón "Enviar"
            window["submit"].update(disabled=True)

            # Get the question from the input
            question = values["question"]

            # Call the OpenAI API to generate a response asynchronously
            thread_event = threading.Event()
            response_thread = threading.Thread(target=generate_response_async, args=(question, window, thread_event))
            response_thread.start()

            # Show a message indicating that we're waiting for a response
            window["response"].update("Esperando respuesta de OpenAI...")
            time.sleep(0.1)
            window.Refresh()

        elif event == "cancel":
            if response_thread.is_alive():
                thread_event.set()
                window["response"].update("Solicitud cancelada.")
                window["question"].update("")

        elif event == '-RESPONSE-':
            # Update the GUI with the response and update the total cost
            response, response_cost = values[event]

            # Volver a activar el botón "Enviar"
            window["submit"].update(disabled=False)

            #window.write_event_value('-LOG-', f"Pregunta: {question}\nRespuesta: {response}\n\n")    
            window["response"].update(response)
            window["question"].update("")
            total_cost += response_cost
            window["total_cost_value"].update(f"{total_cost:.2f}")
            save_total_cost(total_cost, config)

            with open("log.txt", "a") as f:
                f.write(f"Pregunta: {values['question']}\n")
                f.write(f"Respuesta: {values[event][0]}\n\n")
            if response_cost > 17.50:
                sg.popup("Advertencia", f"El coste total acumulado es de ${response_cost:.2f}, superior a $17.50.", location=(None, None))
        elif event == "clear_question":
                # Clear the question input
            window["question"].update("")

        elif event == "clear_response":
                # Clear the response output
            window["response"].update("")

        elif event == "copy_response":
                # Copy the response to the clipboard
            response = values["response"]
            if response:
                pyperclip.copy(response)
        elif event == "about":
            show_about_window()

        elif event == '-LOG-':
            window['log_output'].update(values['log_output']+"\n" + values[event])
            
        elif event == "clear_log":
            window["log_output"].update("")
        elif event == "config":
            show_configuration_window()  # Llama a la función

        elif event == '-ERROR-':
            sg.popup_error(values['-ERROR-'])


    # Close the window when the loop exits
    window.close()


def generate_response(question):
    global message_history  # Accede a la variable global

    # Añade la pregunta del usuario al historial de mensajes
    message_history.append({"role": "user", "content": question})

    MODEL = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=message_history,
        temperature=0.5,
    )

    # Añade la respuesta del modelo al historial de mensajes
    response_text = response.choices[0]['message']['content']
    message_history.append({"role": "assistant", "content": response_text})

    response_cost = response.usage['total_tokens'] * 0.000002  # Assuming $0.0003 per token
    return response_text, response_cost



if __name__ == "__main__":
    main()

# api_key, total_cost = load_config()