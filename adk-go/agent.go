package main

import (
	"flag"
	"fmt"

	"adk-benchmark/src/interfaces"
)

func main() {
	debugFlag := flag.Bool("debug", false, "Włącza podgląd na żywo z myślenia agenta i narzędzi")
	flag.Parse()

	if *debugFlag {
		fmt.Println("\033[1;36m[TRYB DEBUG AKTYWNY]\033[0m")
	}

	interfaces.ExecuteAll(*debugFlag)
}