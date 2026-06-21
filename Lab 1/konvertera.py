
def celsius_to_fahrenheit(t):
    return t * 9 / 5 + 32


def fahrenheit_to_celsius(t):
    return (t - 32) * 5 / 9


def celsius_to_kelvin(t):
    return t + 273.15


def kelvin_to_celsius(t):
    return t - 273.15


def fahrenheit_to_kelvin(t):
    return (t - 32) * 5 / 9 + 273.15


def kelvin_to_fahrenheit(t):
    return (t - 273.15) * 9 / 5 + 32


print("Temperaturkonverteraren")
print("1. Celsius till Fahrenheit")
print("2. Fahrenheit till Celsius")
print("3. Celsius till Kelvin")
print("4. Kelvin till Celsius")
print("5. Fahrenheit till Kelvin")
print("6. Kelvin till Fahrenheit")

val = input("\nVilken konvertering vill du göra? ")

if val == "1":
    temperatur = float(input("\nAnge temperatur i Celsius: "))
    resultat = celsius_to_fahrenheit(temperatur)
    print("Det motsvarar", resultat, "Fahrenheit")
elif val == "2":
    temperatur = float(input("\nAnge en temperatur i Fahrenheit: "))
    resultat = fahrenheit_to_celsius(temperatur)
    print("Det motsvarar", resultat, "Celsius")
elif val == "3":
    temperatur = float(input("\nAnge temperatur i Celsius: "))
    resultat = celsius_to_kelvin(temperatur)
    print("Det motsvarar", resultat, "Kelvin")
elif val == "4":
    temperatur = float(input("\nAnge temperatur i Kelvin: "))
    resultat = kelvin_to_celsius(temperatur)
    print("Det motsvarar", resultat, "Celsius")
elif val == "5":
    temperatur = float(input("\nAnge temperatur i Fahrenheit: "))
    resultat = fahrenheit_to_kelvin(temperatur)
    print("Det motsvarar", resultat, "Kelvin")
elif val == "6":
    temperatur = float(input("\nAnge temperatur i Kelvin: "))
    resultat = kelvin_to_fahrenheit(temperatur)
    print("Det motsvarar", resultat, "Fahrenheit")
else:
    print("Ogiltigt val")
