from core.config import get_settings

from fastapi import FastAPI

# 1. 加载配置信息
settings = get_settings()
print(settings)

app = FastAPI()

def main():
    print("Hello from mini-manus!")

if __name__ == "__main__":
    main()
