from PIL import Image, ImageDraw, ImageFont
import os

def EditImage(nickname, titulo_principal, input_image=None, output_path=None):
    """ El Output es para especificar la ruta de salida, el input no importa mucho ya trae imagen por defecto """
    # Abrir la imagen existente
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if input_image is None:
        input_image = os.path.join(current_dir, 'input.png')
    
    if output_path is None:
        output_path = os.path.join(current_dir, 'output.png')

    try:
        imagen = Image.open(input_image)
    except:
        print("Error al cargar la imagen, usando imagen por defecto")
        imagen = Image.open(os.path.join(current_dir, 'input.png'))
    
    # Crear objeto para dibujar sobre la imagen existente
    dibujo = ImageDraw.Draw(imagen)
    
    try:
        # Para el nickname (aumentado el tamaño)
        tamano_fuente_nick = 55  # Antes era 35
        font = os.path.join(current_dir, 'Arial_Bold.ttf')
        fuente_nick = ImageFont.truetype(font, tamano_fuente_nick)
        
        # Para el título principal
        tamano_fuente_titulo = 65
        fuente_titulo = ImageFont.truetype(font, tamano_fuente_titulo)
    except:
        print("Error al cargar la fuente, usando fuente por defecto")
        fuente_nick = ImageFont.load_default()
        fuente_titulo = ImageFont.load_default()
    
    # Agregar nickname (ajustado posición)
    x_nick = 250  # Aumentado de 150 a 200 para moverlo más a la derecha
    y_nick = 35   # Aumentado de 30 a 45 para bajarlo un poco
    dibujo.text((x_nick, y_nick), nickname, font=fuente_nick, fill='black')
    
    # Preparar el título principal
    palabras = titulo_principal.split()
    lineas = []
    linea_actual = []
    
    # Dividir el texto en líneas manualmente
    for palabra in palabras:
        linea_actual.append(palabra)
        linea_prueba = ' '.join(linea_actual)
        if dibujo.textlength(linea_prueba, font=fuente_titulo) > imagen.width * 0.8:
            linea_actual.pop()
            lineas.append(' '.join(linea_actual))
            linea_actual = [palabra]
    if linea_actual:
        lineas.append(' '.join(linea_actual))
    
    # Calcular altura total del texto y posición inicial
    espacio_entre_lineas = tamano_fuente_titulo * 1.2
    altura_total = len(lineas) * espacio_entre_lineas
    y = (imagen.height - altura_total) // 2 + 50  # Agregado +50 para bajar más el título
    
    # Dibujar cada línea del título
    for linea in lineas:
        ancho_texto = dibujo.textlength(linea, font=fuente_titulo)
        x = (imagen.width - ancho_texto) // 2
        dibujo.text((x, y), linea, font=fuente_titulo, fill='black')
        y += espacio_entre_lineas
    
    # Guardar la imagen editada
    if output_path is None:
        output_path = os.path.join(current_dir, 'output.png')
    
    try:
        imagen.save(output_path)
        print(f"Imagen guardada exitosamente en: {output_path}")
    except Exception as e:
        print(f"Error al guardar la imagen: {str(e)}")

# Ejemplo de uso correcto:
# nickname = "chicodereddit"
# titulo = "Titulo de ejemplo que se espera"
# EditImage(nickname=nickname, 
#          titulo_principal=titulo,
#          input_image="input.png",
#          output_path="output.png")