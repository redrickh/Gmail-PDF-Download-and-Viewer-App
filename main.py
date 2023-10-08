import imaplib
import email
from email.header import decode_header
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
import os
import fitz
from kivy.uix.image import Image

# ...

class PDFViewerPopup(Popup):
    def __init__(self, pdf_image_path, return_callback, **kwargs):
        super(PDFViewerPopup, self).__init__(**kwargs)
        self.title = "PDF Megtekintő"
        self.return_callback = return_callback  # Visszahívási függvény beállítása

        # Az Image widget használatával jelenítjük meg a PNG képet
        self.image_widget = Image(source=pdf_image_path, size_hint=(1, 1), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.image_widget.keep_ratio = False  # Engedjük, hogy a kép méretezhető legyen

        # Hozz létre egy elrendezést a gombokhoz
        button_layout = FloatLayout()

        # Hozz létre egy nagyítás gombot
        zoom_in_button = Button(text="Nagyítás", size_hint=(None, None), pos_hint={'x': 0.05, 'y': 0.05})
        zoom_in_button.bind(on_press=self.zoom_in)
        button_layout.add_widget(zoom_in_button)

        # Hozz létre egy kicsinyítés gombot
        zoom_out_button = Button(text="Kicsinyítés", size_hint=(None, None), pos_hint={'x': 0.8, 'y': 0.05})
        zoom_out_button.bind(on_press=self.zoom_out)
        button_layout.add_widget(zoom_out_button)

        # Hozz létre egy "Vissza" gombot a kezdő ablakhoz való visszatéréshez
        return_button = Button(text="Vissza", size_hint=(None, None), pos_hint={'x': 0.05, 'y': 0.9})
        return_button.bind(on_press=self.return_to_main)
        button_layout.add_widget(return_button)

        # Hozz létre egy FloatLayout-ot, amely tartalmazza a képet és a gombokat
        main_layout = FloatLayout()
        main_layout.add_widget(self.image_widget)
        main_layout.add_widget(button_layout)

        self.content = main_layout

    def zoom_in(self, instance):
        current_size_hint = self.image_widget.size_hint
        new_size_hint = (current_size_hint[0] * 1.1, current_size_hint[1] * 1.1)
        self.image_widget.size_hint = new_size_hint

    def zoom_out(self, instance):
        current_size_hint = self.image_widget.size_hint
        new_size_hint = (current_size_hint[0] / 1.1, current_size_hint[1] / 1.1)
        self.image_widget.size_hint = new_size_hint

    def return_to_main(self, instance):
        # Hívjuk meg a visszahívást a kezdő ablakhoz való visszatéréshez
        if self.return_callback:
            self.return_callback(instance)  # Adjuk át az 'instance' argumentumot
        self.dismiss()

class PDFDownloadAndViewerApp(App):
    def show_main_screen(self, instance):
        self.root.current = "main_screen"

    def build(self):
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=60)

        self.background_color = (0.5, 0.5, 1, 1)  # Világoskék háttérszín

        self.download_button = Button(
            text='PDF letöltése',
            size_hint=(.5, .25),
            on_press=self.download_pdf
        )
        self.layout.add_widget(self.download_button)
        self.downloaded_files = []

        # PDF fájlok listájának megjelenítése
        self.pdf_list = ScrollView()
        self.pdf_list_label = Label()
        self.pdf_list_label.bind(on_touch_down=self.on_pdf_selected)
        self.pdf_list.add_widget(self.pdf_list_label)
        self.layout.add_widget(self.pdf_list)

        # Lista a PNG képek elérési útjaival
        self.png_images = []

        # Ellenőrzés, hogy a PDF fájl már letöltve van-e
        self.check_existing_pdfs()

        return self.layout

    def check_existing_pdfs(self):
        # Ellenőrizd, hogy a jelenlegi munkakönyvtárban található PDF fájlok már letöltve vannak-e
        self.downloaded_files = []
        self.png_images = []
        current_directory = os.getcwd()
        for filename in os.listdir(current_directory):
            if filename.endswith(".pdf"):
                self.downloaded_files.append(filename)
                # Módosítás: Konvertálás PNG képpé és hozzáadás a listához
                pdf_path = os.path.join(current_directory, filename)
                png_image = self.convert_pdf_to_image(pdf_path)
                if png_image:
                    self.png_images.append(png_image)

        # Frissítsd a listát a letöltött PDF fájlok neveivel
        pdf_list_text = "\n".join(self.downloaded_files)
        self.pdf_list_label.text = pdf_list_text

    def download_pdf(self, instance):
        # Gmail fiók bejelentkezése IMAP használatával
        imap_server = imaplib.IMAP4_SSL('imap.gmail.com')
        imap_server.login('redrick555@gmail.com', 'qgjl lmcr ocvm iizy')

        # Kifejezett feladótól érkezett emailek keresése
        desired_sender = 'universzovetkezetizrt@univer.hu'
        search_query = f'(FROM "{desired_sender}")'
        imap_server.select('inbox')
        status, email_ids = imap_server.search(None, search_query)

        # PDF mellékletek letöltése
        for email_id in email_ids[0].split():
            status, email_data = imap_server.fetch(email_id, '(RFC822)')
            raw_email = email_data[0][1]
            msg = email.message_from_bytes(raw_email)

            for part in msg.walk():
                filename = part.get_filename()
                if filename:
                    filename = decode_header(filename)[0][0]
                    if isinstance(filename, bytes):
                        filename = filename.decode('utf-8')
                    # Melléklet mentése az aktuális munkakönyvtárba
                    file_path = os.path.join(os.getcwd(), filename)
                    with open(file_path, 'wb') as pdf_file:
                        pdf_file.write(part.get_payload(decode=True))

                    self.downloaded_files.append(file_path)
                    # Módosítás: Konvertálás PNG képpé és hozzáadás a listához
                    png_image = self.convert_pdf_to_image(file_path)
                    if png_image:
                        self.png_images.append(png_image)

        # Frissítsd a listát a letöltött PDF fájlok neveivel
        self.pdf_texts = self.downloaded_files
        pdf_list_text = "\n".join(self.pdf_texts)
        self.pdf_list_label.text = pdf_list_text

        # IMAP szerverrel való kapcsolat lezárása
        imap_server.logout()

    def on_pdf_selected(self, instance, touch):
        if 'button' in touch.profile and touch.button == 'left':
            # Az érintési pozíció alapján kiszámoljuk az indexet
            touch_y = self.pdf_list_label.to_local(touch.x, touch.y)[1]
            index = int((self.pdf_list_label.height - touch_y) / 20)  # 20 az elemek magassága
            print(f"Kiválasztott index: {index}")

            # Ellenőrizzük, hogy az index helyes
            if 0 <= index < len(self.png_images):
                selected_png_image = self.png_images[index]  # Kiválasztott PNG kép elérési útja

                if selected_png_image:
                    # Hozz létre és jelenítsd meg az új PDF néző ablakot
                    pdf_viewer_popup = PDFViewerPopup(selected_png_image,
                                                      return_callback=lambda instance: self.show_main_screen(instance))
                    pdf_viewer_popup.open()
                else:
                    print("Hiba történt a PNG kép kiválasztása során.")
            else:
                print("Hiba: Érvénytelen index.")

    def convert_pdf_to_image(self, pdf_file_path):
        password = "0oE19w76"  # Add your PDF password here
        output_image_path = pdf_file_path.replace(".pdf", "_page_0.png")  # Kép elérési útja

        try:
            pdf_document = fitz.open(pdf_file_path)
            if pdf_document.is_encrypted:
                pdf_document.authenticate(password)

            # Az első oldal konvertálása PNG képként
            page = pdf_document.load_page(0)
            pix = page.get_pixmap()
            pix.save(output_image_path)

        except Exception as e:
            print(f"Hiba a PDF konvertálása során: {str(e)}")
            return None

        return output_image_path

if __name__ == '__main__':
    PDFDownloadAndViewerApp().run()
