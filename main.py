import sys

def main():
    if "--install" in sys.argv:
        from segunda_etapa import run
    else:
        from preparacao import run

    run()

if __name__ == "__main__":
    main()