from sys import exit

original = 'lorem_ipsum.txt'
print('Palavras contidas no arquivo ' + original + ': ' + str(len(open(original).read().split())))

modificado = '5000K.txt'
quantidade = modificado.replace('.txt', '')

if quantidade.find('K'):
    quantidade = int(quantidade.replace('K', ''))
else:
    exit()

with open(modificado, 'w') as file:
    for i in range(0, int(quantidade/10)):
        print(i)
        file.write(open(original).read())

print('Palavras contidas no arquivo ' + modificado + ': ' + str(len(open(modificado).read().split())))
