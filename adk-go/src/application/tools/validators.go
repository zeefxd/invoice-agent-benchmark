package tools

import (
	"regexp"
	"strconv"
)

type ValidationResult struct {
	Valid   bool   `json:"valid"`
	Message string `json:"message"`
}

func ValidateNip(nip string) ValidationResult {
	re := regexp.MustCompile(`\D`)
	digits := re.ReplaceAllString(nip, "")

	if len(digits) != 10 {
		return ValidationResult{Valid: false, Message: "NIP musi mieć 10 cyfr."}
	}

	weights :=[]int{6, 5, 7, 2, 3, 4, 5, 6, 7}
	checksum := 0
	for i := 0; i < 9; i++ {
		d, _ := strconv.Atoi(string(digits[i]))
		checksum += d * weights[i]
	}
	checksum = checksum % 11

	lastDigit, _ := strconv.Atoi(string(digits[9]))
	if checksum == lastDigit {
		return ValidationResult{Valid: true, Message: "NIP jest poprawny."}
	}
	return ValidationResult{Valid: false, Message: "NIP ma błędną sumę kontrolną."}
}