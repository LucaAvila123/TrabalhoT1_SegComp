# <center> Relatório do Trabalho T1 </center>
## <center>  Segurança em Computação – 2025/2 
## <center> Infraestrutura de Certificação Digital: Let's Encrypt e PKI Própria

---

### Informações do Grupo
- **Disciplina:** Segurança em Computação 2025/2
- **Integrantes:**  
  - Nome: _____________ 
  - Nome: _____________  
  - Nome: _____________  

---

## 1. Arquitetura do Ambiente
Descreva e desenhe (use figuras) a arquitetura geral dos dois cenários implementados, destacando suas diferenças principais:

- **Cenário 1:** Let's Encrypt + ngrok — uso de uma autoridade certificadora pública para emissão automática de certificados válidos por meio do protocolo ACME.  
- **Cenário 2:** PKI própria (Root + Intermediária) — criação e operação de uma infraestrutura de chaves públicas local, com emissão de certificados assinados por uma CA interna.

---

## 2. Tarefa 1 – HTTPS com Certificado Público (Let's Encrypt + ngrok)

### 2.1. Preparação do Ambiente
- Sistema operacional: Windows 11 / Ubuntu  
- Ferramentas utilizadas: Docker, Ngrok, VSCode, Navegador Web  
- Versão do Docker / Nginx: Docker 28.5.1 , Nginx 1.27 

O ambiente foi configurado usando containers dockerizados. Dois serviços foram disponibilizados: 
- Nginx: Servidor Web responsável por mostrar a página HTML. A página de exemplo é [index.html](task1/nginx/html/index.html), e é configurada pelo arquivo [nginx.conf](/task1/nginx/nginx.conf).
- Ngrok: Serviço de tunelamento que expõe a porta local para a internet.

### 2.2. Exposição com ngrok
- Domínio público gerado: [Index Page](https://turbanlike-corie-snowily.ngrok-free.dev/) 

O Ngrok serviu como um proxy reverso com terminação TLS. O serviço faz automaticamente o processo de validação de domínio, e usa o Let's Encrypt para validar. Com isso, o certificado público é emitido e gerenciado nos servidores do ngrok, que serviram para encaminhar o tráfego para o ambiente local, pelo túnel criado. Isso permitiu com que uma rede local em HTTPS seja acessada por fora apenas com uma conexão HTTPS confiável.

### 2.3. Emissão do Certificado
- Caminho do certificado gerado: 

- - [/task1/server/server_fullchain.pem](/task1/server/server_fullchain.pem) (Final + Intermediário) 
- - [/task1/ca/root/rootCA.cert.pem](/task1/ca/root/rootCA.cert.pem) (CA Raiz) 


Os certificados foram gerados usando a biblioteca `criptography` do Python. Para a emissão, o processo utilizado foi dividido em etapas. A primeira foi gerar uma chave RSA de 4096 bits e um certificado `rootCA.cert.pem` que é válido por 10 anos, sendo a **CA Raiz**. Em seguida, foi gerado uma CSR que foi assinada pela chave da CA Raiz, gerando o certificado intermediário `intermediateCA.cert.pem`. Por fim, foi gerado o certificado do servidor. Foi gerado um par de chaves para o `localhost`, foi gerado uma CSR que foi assinada pela CA intermediária. O script consolidou os dois certificados no arquivo `server_fullchain.pem`.

Para a validação, foi utilizado um script python ([verify.py](/task1/app/verify.py)), que imprime `ÒK` caso o TLS seja corretamente estabelecido.

### 2.4. Configuração HTTPS no Nginx

O servidor foi configurado usando o arquivo [nginx.conf](/task1/nginx/nginx.conf). Nele, foi configurado o suporte a somente conexões HTTPS via `listen 443 ssl;`. Para que o certificado emitido seja aceito, foi apontado os caminhos para a chave privada e para o certificado do servidor + CA Intermediária, com as linhas:
```
    ssl_certificate     /etc/nginx/certs/server_fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/server.key.pem;
```


### 2.5. Resultados e Validação
- URL de acesso:
- - Local: https://localhost:8443/
- - Ngrok: https://turbanlike-corie-snowily.ngrok-free.dev/

- Screenshot da página HTTPS: *(inserir imagem)*  
- - Local:
![Local](/task1/images/task1_local.png)
- - Ngrok:
![Ngrok](/task1/images/task1_ngrok.png)
- Resultado do comando de verificação: 
`[OK] TLS estabelecido. Sujeito: ((('countryName', 'BR'),), (('organizationName', 'UFES'),), (('commonName', 'localhost'),))`
- Screenshot do certificado no navegador (cadeado):
- - Local:
![Local](/task1/images/task1_cadeado_local.png)
- - Ngrok:
![Ngrok](/task1/images/task1_cadeado_ngrok.png)
---

## 3. Tarefa 2 – HTTPS com PKI Própria (Root + Intermediária)

### 3.1. Criação da CA Raiz
A CA Raiz possui o papel de ser a base da confiança primária e superior em toda as etapas de certificação. Sua função é assinar a CA intermediária e garantir a sua validade, e este por sua vez, serve para assinar os certificados finais enviados para a web.

O processo de criação começa gerando uma chave privada RSA de 4096 bits:
```
openssl genrsa -out ca/root/rootCA.key.pem 4096
```
E em seguida é gerado o certificado. Um detalhe é que a chave assina a si mesma, tornando-se certificada:
```
openssl req -x509 -new -nodes -sha256 -days 3650 \
  -key ca/root/rootCA.key.pem \
  -subj "/C=BR/O=UFES/CN=UFES Root CA" \
  -out ca/root/rootCA.cert.pem
```

 A importância da CA Raiz na cadeia de confiança se dá pelo fato da confiança ser estabelecida logo no começo da certificação. Dessa forma, qualquer certificado só vai poder ser considerado confiável se ele comprovar que foi assinado pela CA Raiz, que já é de confiança.


### 3.2. Criação da CA Intermediária
A CA Raiz é a chave mais crítica da certificação. Se ela for comprometida, toda a cadeia se torna comprometida. A CA intermediária serve justamente para adicionar uma camada de proteção para a CA Raiz. Dessa forma, a CA Raiz pode ser isolada da cadeia. Caso a CA intermediária seja comprometida, bastaria que ela seja revogada, e com a CA Raiz, criar uma nova CA intermediária certificada.

Na criação da CA intermediária, uma chave RSA de 4096 bits é gerada:
```
openssl genrsa -out ca/intermediate/intermediateCA.key.pem 4096
```

E diferente da CA Raiz, a CA intermediária não assina a si mesmo. Neste caso, ela solicita a assinatura do seu certificado para a CA Raiz:
```
openssl req -new -sha256 \
  -key ca/intermediate/intermediateCA.key.pem \
  -subj "/C=BR/O=UFES/CN=UFES Intermediate CA" \
  -out ca/intermediate/intermediateCA.csr.pem
```

Depois, a CA raiz assina com a chave privada o certificado da CA intermediária:
```
openssl x509 -req -in ca/intermediate/intermediateCA.csr.pem \
  -CA ca/root/rootCA.cert.pem -CAkey ca/root/rootCA.key.pem -CAcreateserial \
  -out ca/intermediate/intermediateCA.cert.pem -days 3650 -sha256 \
  -extfile ca/intermediate/ca_ext.cnf
```

### 3.3. Emissão do Certificado do Servidor
- Caminho do `fullchain.crt`: [/task2/server/server_fullchain.pem](/task2/server/server_fullchain.pem)
- Descreva o processo de emissão do certificado do servidor e como ele foi assinado pela CA intermediária.

Para a emissão do certificado do servidor, foi gerado uma chave privada RSA de 4096 bits:
```
openssl genrsa -out server/server.key.pem 4096
```
Um arquivo SAN foi criado para definir quais as propriedades que esse certificado terá. Aqui foi definido o domínio `localhost`, e que esse certificado não poderá assinar outros certificados.
```
cat > server/san.cnf <<'EOF'
subjectAltName=DNS:localhost
basicConstraints=critical,CA:false
keyUsage=critical,digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
EOF
```

Em seguida, é solicitado que a CA intermediária assine o certificado posteriormente:
```
openssl req -new -sha256 \
  -key server/server.key.pem \
  -subj "/C=BR/O=UFES/CN=localhost" \
  -out server/server.csr.pem
```

E a CA intermediária faz a assinatura do certificado do servidor:
```
openssl x509 -req -in server/server.csr.pem \
  -CA ca/intermediate/intermediateCA.cert.pem \
  -CAkey ca/intermediate/intermediateCA.key.pem -CAcreateserial \
  -out server/server.cert.pem -days 365 -sha256 \
  -extfile server/san.cnf
```

Por fim, o arquivo `server_fullchain.pem` foi gerado, concatenando o `server.cert.pem` e o `intermediateCA.cert.pem` para ser usado no nginx.


### 3.4. Importação da CA Raiz no Navegador
Descreva o procedimento adotado para importar o certificado raiz no navegador:  
- Caminho seguido no navegador: __________________________  
- Resultado esperado: navegador passou a confiar na CA criada? Justifique
- Inclua uma captura de tela do certificado confiável.

### 3.5. Validação da Cadeia
- Resultado do comando de verificação: ____________________________  
- Screenshot do navegador com HTTPS ativo e confiável: *(inserir imagem)*

---

## 4. Comparação entre os Dois Cenários
Responda às questões abaixo com base na experiência prática:

- Quais as principais diferenças entre o uso de certificados públicos e privados?  
- Em quais cenários cada abordagem é mais adequada?  
- Por que a importação da CA raiz é necessária no segundo cenário?  

---

## 5. Conclusões
- Apresente as principais lições aprendidas durante o projeto.  
- Explique a importância prática da certificação digital e da confiança em ambientes seguros.

---

## Checklist Final
| Item | Status |
|------|--------|
| Servidor Nginx funcional (Docker) | ✅ / ❌ |
| Certificado Let's Encrypt emitido e válido | ✅ / ❌ |
| PKI própria criada (Root + Intermediária) | ✅ / ❌ |
| Importação da CA raiz no navegador | ✅ / ❌ |
| Cadeia de certificação validada com sucesso | ✅ / ❌ |
| Relatório completo e entregue | ✅ / ❌ |
| Apresentação prática (vídeo) | ✅ / ❌ |

---


