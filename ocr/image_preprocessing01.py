import matplotlib.pyplot as plt

# 1. Upload any sample document image to your Colab workspace sidebar
# 2. Put its filename here to run the function:
sample_path = "/content/WhatsApp Image 2026-06-30 at 23.52.48.jpeg"

try:
    processed_result = enhance_medical_image(sample_path)

    # Display the processed, high-contrast black-and-white output
    plt.figure(figsize=(10, 10))
    plt.imshow(processed_result, cmap='gray')
    plt.title("Preprocessed Clean Image for OCR")
    plt.axis('off')
    plt.show()

except Exception as e:
    print(f"Please upload an image first! Error: {e}")
