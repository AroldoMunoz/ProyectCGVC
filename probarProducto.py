import os
import cvzone
import cv2
import math
from cvzone.PoseModule import PoseDetector

# Cambiar la fuente de video a cámara
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Configurar el ancho de la cámara
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Configurar la altura de la cámara

detector = PoseDetector()

shirtFolderPath = "Resources/Shirts"
listShirts = os.listdir(shirtFolderPath)
fixedRatio = 262 / 190  # Proporción de la camisa respecto a los puntos de referencia
shirtRatioHeightWidth = 581 / 440  # Proporción de altura/ancho de la camisa
imageNumber = 0
talla_tabla = {
    "S": {"distancia_hombros_caderas": (0, 60)},  # Valores en pixeles
    "M": {"distancia_hombros_caderas": (61, 80)},
    "L": {"distancia_hombros_caderas": (81, 100)},
}

def determinar_talla(dist_hombros, dist_caderas, altura_estimada):
    """Determina la talla en base a las distancias relativas del cuerpo."""
    dist_hombros_caderas = abs(dist_hombros - dist_caderas)

    for talla, rango in talla_tabla.items():
        if rango["distancia_hombros_caderas"][0] <= dist_hombros_caderas <= rango["distancia_hombros_caderas"][1]:
            return talla
    return "Desconocida"

# Cargar botones y ajustarlos
imgButtonRight = cv2.imread("Resources/button.png", cv2.IMREAD_UNCHANGED)
imgButtonRight = cv2.resize(imgButtonRight, (0, 0), fx=0.5, fy=0.5)
imgButtonLeft = cv2.flip(imgButtonRight, 1)  # Botón invertido para la izquierda

counterRight = 0
counterLeft = 0
selectionSpeed = 10  # Velocidad de selección de imagen

cv2.namedWindow("Image", cv2.WINDOW_NORMAL)  # Permitir cambiar el tamaño
cv2.resizeWindow("Image", 1280, 720)  # Establecer tamaño de ventana en 640x480

while True:
    success, img = cap.read()
    if not success:
        print("No se puede acceder a la cámara.")
        break
    
    img = cv2.flip(img, 1)
    img = detector.findPose(img)  # Detectar pose
    lmList, bboxInfo = detector.findPosition(img, bboxWithHands=False, draw=False)
   
    if lmList:
        # Coordenadas de referencia
        lm11 = lmList[11][0:2]  # Hombro izquierdo
        lm12 = lmList[12][0:2]  # Hombro derecho
        lm23 = lmList[23][0:2]  # Cadera izquierda
        lm24 = lmList[24][0:2]  # Cadera derecha
        lm0 = lmList[0][0:2]    # Cabeza
        lm27 = lmList[27][0:2]  # Pies

        imgShirt = cv2.imread(os.path.join(shirtFolderPath, listShirts[imageNumber]), cv2.IMREAD_UNCHANGED)

        # Calcular ancho y alto de la camisa basado en los puntos 11 y 12
        widthOfShirt = int((lm11[0] - lm12[0]) * fixedRatio)
        imgShirt = cv2.resize(imgShirt, (widthOfShirt, int(widthOfShirt * shirtRatioHeightWidth)))

        # Calcular las distancias entre los puntos clave
        dist_hombros = abs(lm11[0] - lm12[0])
        dist_caderas = abs(lm23[0] - lm24[0])
        altura_estimada = abs(lm0[1] - lm27[1])  # Distancia vertical (altura estimada)
        # Determinar la talla en función de las distancias calculadas
        talla_sugerida = determinar_talla(dist_hombros, dist_caderas, altura_estimada)

        # Ajustar escala y posición
        currentScale = (lm11[0] - lm12[0]) / 190
        offset = int(44 * currentScale), int(48 * currentScale)

        try:
            img = cvzone.overlayPNG(img, imgShirt, (lm12[0] - offset[0], lm12[1] - offset[1]))
        except:
            pass

        # Posicionar botones
        img = cvzone.overlayPNG(img, imgButtonRight, (550, 200))  # Botón derecho
        img = cvzone.overlayPNG(img, imgButtonLeft, (25, 200))    # Botón izquierdo

        # Detectar selección de botones
        if lmList[15][0] > 500: # Botón derecho
            counterRight += 1
            cv2.ellipse(img, (580, 230), (40, 40), 0, 0,
                        counterRight * selectionSpeed, (0, 255, 0), 10)
            if counterRight * selectionSpeed > 360:
                counterRight = 0
                if imageNumber < len(listShirts) - 1:
                    imageNumber += 1
        elif lmList[16][0] < 50: # Botón izquierdo
            counterLeft += 1
            cv2.ellipse(img, (60, 230), (40, 40), 0, 0,
                        counterLeft * selectionSpeed, (0, 255, 0), 10)
            if counterLeft * selectionSpeed > 360:
                counterLeft = 0
                if imageNumber > 0:
                    imageNumber -= 1
        else:
            counterRight = 0
            counterLeft = 0

    # Dibujar cuadro en la parte inferior para la talla sugerida
    h, w, _ = img.shape
    cv2.rectangle(img, (0, h - 80), (w, h), (50, 50, 50), -1)  # Fondo gris oscuro
    cv2.putText(img, f"Te sugiero talla: {talla_sugerida}",
                (20, h - 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    # Mostrar la ventana
    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == 27:  # Salir con la tecla Esc
        print("Saliendo...")
        break

cap.release()
cv2.destroyAllWindows()
