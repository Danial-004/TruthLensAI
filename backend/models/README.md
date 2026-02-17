# ML Models for TruthLens AI

This directory is intended for storing custom, fine-tuned machine learning models.

## 🤖 Default Models

By default, the application **does not require any files in this directory**. The necessary models are automatically downloaded from the [Hugging Face Hub](https://huggingface.co) upon first launch and cached locally.

The default models used are:
1.  **Classification Model**: `xlm-roberta-base`
    - Used for multilingual fake/real news classification.
2.  **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
    - Used for calculating semantic similarity between the user's text and web search results.

## 🚀 Using a Custom Fine-Tuned Model

The application is designed to automatically prioritize a local fine-tuned model if one is available. This allows for improved accuracy based on your own training data.

To use a custom model:
1.  Train your model using a library like `transformers` on a labeled fake news dataset.
2.  Save the trained model (including `config.json`, `pytorch_model.bin`, and tokenizer files) into a subdirectory within this `models/` folder. For example:
    ```
    models/
    └── truthlens_model_v1/
        ├── config.json
        ├── pytorch_model.bin
        ├── tokenizer_config.json
        └── ... (other model files)
    ```
3.  The `backend/model.py` script is pre-configured to automatically detect and load a model from a local path named `models/truthlens_model` if it exists, instead of downloading the base model from the web.

This setup provides a seamless way to upgrade the AI core of the application without changing the code.