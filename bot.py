import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pytesseract
from PIL import Image
import numpy as np
import easyocr
import sys
import cv2


# def match_digit(digit_image):
#     # digit_image_gray = cv2.cvtColor(digit_image, cv2.COLOR_BGR2GRAY)  # Ensure image is grayscale

#     # Initialize a dictionary to hold match scores
#     match_scores = {}

#     # Compare with each digit template
#     for digit, template in digit_templates.items():
#         res = cv2.matchTemplate(digit_image, template, cv2.TM_CCOEFF_NORMED)
#         min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
#         match_scores[digit] = max_val  # Store the best match score for each digit

#     # Return the digit with the highest match score
#     best_match_digit = max(match_scores, key=match_scores.get)
    
#     # If no significant match, treat as empty (low match score)
#     if match_scores[best_match_digit] < 0.5:  # You can adjust this threshold
#         return None  # Indicates empty cell
#     return best_match_digit
# Initialize the WebDriver

def preprocess_block(cell_image):
    gray_image = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

    # Apply binary thresholding
    _, binary_image = cv2.threshold(gray_image, 200, 255, cv2.THRESH_BINARY_INV)
    # binary_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # Denoise the image (optional based on the quality of the block)
    denoised_image = cv2.fastNlMeansDenoising(binary_image, None, 30, 7, 21)

    return denoised_image

driver = webdriver.Chrome()

# Open a webpage
url = sys.argv[1]
driver.get(url)

time.sleep(2)  # Wait for expert mode to load
gameTable = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "game"))
    )
canvas = gameTable.find_element(By.TAG_NAME, "canvas")
pixels = driver.execute_script("""
var canvas = arguments[0];
var context = canvas.getContext('2d');
var imageData = context.getImageData(0, 0, canvas.width, canvas.height);
return imageData.data;
""", canvas)

# Convert the pixels into a NumPy array (for easier manipulation)
reader = easyocr.Reader(['en'])

# digit_templates = {}
# for digit in range(1,10):
#     template = cv2.imread(f'reference_digits/{digit}.png', cv2.IMREAD_GRAYSCALE)
#     digit_templates[digit] = template

width = 2000
height = 2000
pixels_array = np.array(pixels).reshape((height, width, 4))  # RGBA format
pixels_array = pixels_array.astype(np.uint8)

binary = preprocess_block(pixels_array)


# Save or display the processed image to check
# cv2.imwrite("black_digits.png", binary)

# 2. Identify the cell boundaries (assuming each cell is of equal size)
cell_width = binary.shape[1] // 9 
cell_height = binary.shape[0] // 9 

# pixels now contains the RGBA values (each value is a byte: 0-255 range)
# Example: Accessing the first pixel's RGBA values
cell_offset_x = 10 # Fine-tune this based on the misalignment
cell_offset_y = 10  # Fine-tune this as well

# Loop through each cell in the 9x9 grid
cells = []
for row in range(9):
    for col in range(9):
        # Calculate the boundaries of the current cell, adjusting with offsets
        x1 = col * cell_width + cell_offset_x
        y1 = row * cell_height + cell_offset_y
        x2 = (col + 1) * cell_width - cell_offset_x
        y2 = (row + 1) * cell_height - cell_offset_y

        # Extract the cell image from the grid
        cell_image = binary[y1:y2, x1:x2]

        # cv2.imwrite(f"sudoku_{row}_{col}.png", cell_image)

        # Extract text (digit) from the processed cell
        # digit = pytesseract.image_to_string(cell_image, config="--oem 3 --psm 6 -c tessedit_char_whitelist=123456789")
        result = reader.readtext(cell_image, detail=0, allowlist='123456789')
        # print(f"Cell [{row}, {col}] digit: {result}")
        if result:
            if (result[0] == '7'):
                digit = pytesseract.image_to_string(cell_image, config="--oem 3 --psm 6 -c tessedit_char_whitelist=123456789")
                cells.append(digit.strip())
            else:
                cells.append(result[0]) 
        else:
            cells.append('.')


# Reshape the list to match a 9x9 Sudoku board
sudoku_board = np.array(cells).reshape((9, 9))

def solveS(board, i, j):
    if i == len(board):
        return True
    if j == len(board):
        return solveS(board,i+1,0)
    
    if board[i][j] != '.' :
        return solveS(board,i,j+1)
    
    for char in range(1, 10):
        if helper(board,i, j,str(char)):  
            board[i][j] = str(char)
            if (solveS(board,i,j+1)):
                return True
            board[i][j] = '.'
    return False

def helper(board, r, c, val):
    for i in range(9):
        if (board[i][c]==val):
            return False

    for i in range(9):
        if (board[r][i]==val):
            return False
    newI = (r//3)*3
    newJ= (c//3)*3
    for i in range(newI, newI + 3):
        for j in range(newJ, newJ + 3):
            if (not (i==r and j==c) and board[i][j] == val):
                return False 
    return True

solveS(sudoku_board, 0, 0)

cell_coordiantes = []
cell_coordiantes_full = []
canvas_rect = canvas.rect
canvas_x, canvas_y = canvas_rect["x"], canvas_rect["y"]  # Top-left corner

cell_res = canvas_rect['width'] // 9
cell_he = canvas_rect['height'] // 9
# print(canvas_rect)
for row in range(9):
    for col in range(9):
        x = (2*col+1)/2*cell_he
        y = (2*row+1)/2*cell_res
        full_x = col*cell_height + cell_height//2
        full_y = row*cell_width + cell_width//2
        cell_coordiantes.append((x,y))
        cell_coordiantes_full.append((full_x,full_y))
for row in range(9):
    for col in range(9):
        canvas = gameTable.find_element(By.TAG_NAME, "canvas")
        canvas_rect = canvas.rect
        x, y = cell_coordiantes[row*9 + col]
        full_x, full_y = cell_coordiantes_full[row*9 + col]
        sudoku_board_int = sudoku_board.astype(int)
        answer = sudoku_board_int[row,col]
        # print(answer, x, y)
        action = ActionChains(driver)
        action.move_to_element_with_offset(canvas, x - (canvas_rect['width'] // 2), y - (canvas_rect['height'] // 2)).click().perform()


        # Input the number (you may need to use JavaScript to simulate typing)
        # Here I assume an input box is focused after clicking the canvas. 
        # If not, you will need to use JavaScript to set the value.

        # script = """
        #         # var canvas = arguments[0];
        #         # var answer = arguments[1];
        #         # var ctx = canvas.getContext('2d');
                
        #         # // Draw the number on the canvas at the specified position
        #         # ctx.font = '30px Arial';  // Adjust font size as needed
        #         # ctx.fillStyle = 'black';  // Set text color
        #         # ctx.clearRect(arguments[2], arguments[3], 50, 50);  // Clear previous value (if any)
        #         # ctx.fillText(answer, arguments[2], arguments[3]);  // Draw the new text at position (x, y)
                
        #         # // Optionally, trigger a keypress event for visualization (but not needed for this task)
        #         var event = new KeyboardEvent('keydown', {
        #             bubbles: true,
        #             cancelable: true,
        #             key: answer
        #         });
        #         canvas.dispatchEvent(event);
        #     """
            # Pass the canvas element, answer text, and the cell location
        driver.find_element(By.TAG_NAME, "body").send_keys(str(answer))
        
        time.sleep(0.5)

input("Press Enter to close the browser...")
driver.quit()
