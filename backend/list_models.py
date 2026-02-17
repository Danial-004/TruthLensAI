import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("AIzaSyA2Ssaui-hmoMKbmIVOweM3TseBDEOHj6w"))

models = genai.list_models()
print("Available models:")
for model in models:
    print(model)
