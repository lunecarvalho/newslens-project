# NewsLens

> **Análise e classificação de notícias falsas em português utilizando Processamento de Linguagem Natural e Aprendizado de Máquina.**

O **NewsLens** é um projeto acadêmico de Ciência de Dados que investiga padrões linguísticos presentes em notícias falsas e verdadeiras e aplica técnicas de **Processamento de Linguagem Natural (NLP)** e **Machine Learning** para realizar sua classificação.

O projeto envolve desde a análise exploratória e o pré-processamento do corpus até a comparação entre diferentes algoritmos de classificação. Após os experimentos, o **BERTimbau** foi selecionado como modelo principal do NewsLens.

---

## Objetivo

O NewsLens tem como objetivo desenvolver uma aplicação capaz de analisar textos jornalísticos e classificá-los como:

* 🔴 **Falsa**
* 🟢 **Verdadeira**

Além da classificação, o projeto busca compreender quais características linguísticas, lexicais e temáticas aparecem no corpus e como diferentes modelos de Machine Learning aprendem esses padrões.

> O NewsLens é uma ferramenta experimental de classificação textual e não substitui serviços profissionais de checagem de fatos.

---

## Modelo

O modelo final do projeto utiliza o **BERTimbau Base**:

```text
neuralmind/bert-base-portuguese-cased
```

O BERTimbau é uma versão do BERT pré-treinada para **português brasileiro**.

Após o fine-tuning para classificação binária:

```text
0 → Falsa
1 → Verdadeira
```

o modelo foi publicado no Hugging Face:

**NewsLens BERTimbau**
https://huggingface.co/lunecarvalho/newslens-bertimbau

---

## Dataset

O projeto utiliza dados derivados do **Fake.Br Corpus**, um corpus de notícias falsas e verdadeiras em português.

Após as etapas de preparação e pré-processamento, o conjunto utilizado nos experimentos contém:

```text
7.199 notícias
```

A distribuição entre as classes é aproximadamente balanceada:

| Classe     | Quantidade |
| ---------- | ---------: |
| Falsa      |      3.600 |
| Verdadeira |      3.599 |

Para o experimento final com BERTimbau, os dados foram divididos de forma estratificada:

| Conjunto  | Proporção | Amostras |
| --------- | --------: | -------: |
| Treino    |       80% |    5.759 |
| Validação |       10% |      720 |
| Teste     |       10% |      720 |

O conjunto final de teste possui **360 notícias falsas e 360 verdadeiras**.

---

## Metodologia

O desenvolvimento do projeto foi organizado em diferentes etapas.

### 1. Análise exploratória

Inicialmente foram analisados:

* distribuição das classes;
* tamanho dos textos;
* valores ausentes e duplicados;
* frequência de palavras;
* unigramas e bigramas;
* TF-IDF;
* distribuição temática;
* diferenças lexicais entre notícias falsas e verdadeiras.

A análise mostrou um corpus fortemente concentrado em notícias relacionadas à **política**, além de diferenças lexicais e estilísticas entre as duas classes.

---

### 2. Pré-processamento

Entre as técnicas utilizadas durante os experimentos estão:

* normalização de espaços;
* remoção de HTML;
* remoção de URLs;
* normalização de caracteres;
* conversão para minúsculas em experimentos específicos;
* remoção de acentos para modelos clássicos;
* tokenização;
* lematização experimental;
* reconhecimento de entidades para preservação de nomes próprios.

Diferentes representações textuais foram mantidas porque modelos clássicos e Transformers possuem necessidades distintas de pré-processamento.

---

### 3. Modelagem de tópicos

O **BERTopic** foi utilizado para explorar os principais assuntos presentes no corpus.

Os tópicos encontrados foram posteriormente agrupados em categorias como:

* Política
* Segurança
* Corrupção
* Internacional
* Economia
* Entretenimento
* Saúde
* Sociedade
* Cultura
* Religião
* Tecnologia
* Ciência
* Educação
* Meio Ambiente

Essa etapa foi utilizada para análise exploratória e interpretação dos dados, e não como variável de entrada do classificador final.

---

### 4. Modelos clássicos

Foram avaliados modelos tradicionais de Machine Learning utilizando representações **TF-IDF**:

* Regressão Logística
* Multinomial Naive Bayes
* Linear SVM

O **Linear SVM** apresentou o melhor desempenho entre os modelos clássicos e foi utilizado como principal baseline para comparação com o Transformer.

Também foram realizados:

* validação cruzada estratificada;
* `Pipeline` com TF-IDF;
* busca de hiperparâmetros com `GridSearchCV`;
* análise da matriz de confusão;
* análise dos pesos das features;
* análise qualitativa dos erros.

---

### 5. BERTimbau

Após os experimentos com modelos clássicos, foi realizado o fine-tuning do:

```text
neuralmind/bert-base-portuguese-cased
```

Configuração principal:

| Parâmetro                | Valor                 |
| ------------------------ | --------------------- |
| Épocas                   | 3                     |
| Learning rate            | 2e-5                  |
| Batch size               | 8                     |
| Weight decay             | 0.01                  |
| Maximum sequence length  | 512                   |
| Precisão                 | BF16                  |
| Seleção do melhor modelo | F1-score da validação |

O conjunto de teste final permaneceu separado do treinamento e da seleção do melhor checkpoint.

---

## Resultados

Os modelos finais foram avaliados nas **mesmas 720 notícias** do conjunto de teste.

| Modelo        |   Accuracy |  Precision |     Recall |   F1-score |
| ------------- | ---------: | ---------: | ---------: | ---------: |
| Linear SVM    |     92,22% |     91,30% |     93,33% |     92,31% |
| **BERTimbau** | **99,44%** | **99,72%** | **99,17%** | **99,44%** |

> Precision, Recall e F1-score da tabela consideram a classe `Verdadeira` como classe positiva.

### Matriz de confusão — BERTimbau

|                     | Predita Falsa | Predita Verdadeira |
| ------------------- | ------------: | -----------------: |
| **Real Falsa**      |       **359** |              **1** |
| **Real Verdadeira** |         **3** |            **357** |

O BERTimbau classificou corretamente:

```text
716 de 720 notícias
```

resultando em apenas **4 classificações incorretas**.

Para a classe **Falsa**, foram obtidos:

| Métrica | Resultado |
| Métrica | Resultado |
|---|---:|
| Precision | 99,17% |
| Recall | **99,72%** |
| F1-score | 99,45% |

Das **360 notícias falsas**, **359 foram corretamente identificadas**.

---

## Análise dos resultados

Embora o BERTimbau tenha apresentado desempenho elevado no conjunto de teste, a análise exploratória e os experimentos com o Linear SVM mostraram que o corpus possui padrões relacionados a:

- estilo de escrita;
- vocabulário;
- expressões temporais;
- instituições;
- fontes jornalísticas;
- estrutura textual.

Isso significa que parte do desempenho pode estar relacionada a características específicas do dataset.

Por esse motivo, os **99,44% de accuracy não devem ser interpretados como uma taxa de acerto para qualquer notícia disponível na internet**.

A validação futura com notícias externas ao Fake.Br Corpus é uma etapa importante para avaliar a capacidade de generalização do modelo.

---

## 🤗 Modelo no Hugging Face

O modelo treinado está disponível publicamente no Hugging Face:

**[lunecarvalho/newslens-bertimbau](https://huggingface.co/lunecarvalho/newslens-bertimbau)**

Ele pode ser carregado diretamente com a biblioteca Transformers:

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "lunecarvalho/newslens-bertimbau"

tokenizer = AutoTokenizer.from_pretrained(model_name)

model = AutoModelForSequenceClassification.from_pretrained(
    model_name
)
```

---

## Tecnologias

### Entrada de notícias na aplicação

O NewsLens aceita texto inserido manualmente e URL de uma página de notícia.
No caso de URL, a aplicação extrai o conteúdo textual da página e o envia ao
mesmo modelo de classificação utilizado na análise manual. Trata-se de classificação
textual, não de verificação factual ou avaliação da reputação do domínio.

O módulo `app/extrator_noticia.py` usa Trafilatura para obter o conteúdo principal
e, quando disponíveis, título, autor e data. Textos vazios ou claramente insuficientes
não são classificados. Sites com login, paywall, bloqueios ou conteúdo dependente de
JavaScript podem não permitir a extração; não há tentativa de contornar essas restrições.

São aceitas URLs HTTP/HTTPS sem credenciais. Todos os IPs retornados pelo DNS precisam
ser públicos, e a conexão utiliza o IP validado, mantendo Host e validação TLS do domínio.
Cada redirect é validado novamente (máximo de três). O download aceita HTML/XHTML/texto,
limita o corpo a 3 MiB e usa timeouts de DNS, conexão e leitura de 5 segundos, com orçamento
de 25 segundos para o download e verificações entre leituras. Uma leitura em andamento
pode consumir até seu timeout. Compressão não solicitada é recusada.

Não há cache de artigos, histórico, banco de dados ou persistência permanente de URL/texto.
O conteúdo permanece apenas em memória durante a sessão; “Nova análise” limpa o estado
da análise anterior. O modelo e seu truncamento em 512 tokens permanecem iguais.

Instale as dependências da aplicação com `pip install -r requirements.txt`.
Se Trafilatura ainda não estiver instalada, execute `pip install trafilatura`.
Os testes usam `unittest`, incluído no Python: `python -m unittest discover -s tests -v`.
As respostas HTTP são simuladas; a integração usa Streamlit AppTest e um classificador
simulado, sem baixar pesos ou depender de sites reais.

Referências de implementação: [extração com Trafilatura](https://trafilatura.readthedocs.io/en/latest/corefunctions.html)
e [conexão HTTPS por IP com hostname preservado](https://urllib3.readthedocs.io/en/stable/advanced-usage.html#custom-sni-hostname).

O projeto utiliza principalmente:

### Linguagem

- Python

### Análise de dados

- Pandas
- NumPy
- Matplotlib
- Seaborn

### Processamento de Linguagem Natural

- NLTK
- spaCy
- BERTopic
- TF-IDF
- Hugging Face Transformers

### Machine Learning

- Scikit-learn
- Logistic Regression
- Multinomial Naive Bayes
- Linear SVM

### Deep Learning

- PyTorch
- BERT
- BERTimbau

### Desenvolvimento

- Google Colab
- Git
- GitHub
- Hugging Face

---

## 📁 Estrutura do projeto

```text
newslens-project/
│
├── datasets/
│   └── datasets utilizados e processados
│
├── notebooks/
│   ├── análise exploratória
│   ├── pré-processamento
│   ├── modelos clássicos
│   └── BERTimbau
│
├── results/
│   └── métricas e análises dos modelos
│
├── app/
│   └── aplicação NewsLens
│
├── README.md
└── LICENSE
```

> A estrutura pode sofrer alterações conforme o desenvolvimento da aplicação.

---

## Status do projeto

O projeto encontra-se em desenvolvimento.

### Concluído

- Análise exploratória do dataset
- Pré-processamento textual
- Análise de unigramas e bigramas
- TF-IDF
- Modelagem de tópicos com BERTopic
- Treinamento dos modelos clássicos
- Validação cruzada do Linear SVM
- Análise de erros
- Fine-tuning do BERTimbau
- Avaliação final do BERTimbau
- Publicação do modelo no Hugging Face

### Em desenvolvimento

- Integração do BERTimbau com o NewsLens
- Desenvolvimento da interface web
- Testes com notícias externas ao corpus
- Melhorias na interpretabilidade das previsões

---

## ⚠️ Limitações

O NewsLens é um projeto acadêmico e experimental.

A classificação realizada pelo modelo é baseada nos padrões aprendidos durante o treinamento e **não representa uma verificação factual da notícia**.

O modelo:

- não consulta fontes externas;
- não realiza fact-checking em tempo real;
- não verifica evidências ou documentos;
- pode apresentar desempenho diferente em notícias externas ao dataset;
- pode reproduzir padrões e vieses presentes nos dados de treinamento.

Os resultados devem, portanto, ser utilizados como apoio à análise e não como determinação definitiva da veracidade de uma informação.

---

## Próximos passos

Entre as próximas etapas do projeto estão:

- integração do modelo com Streamlit;
- análise de notícias inseridas pelo usuário;
- avaliação com dados externos;
- análise de explicabilidade do modelo;
- estudo de calibração das previsões;
- expansão das análises linguísticas.

---

## Referências

- Fake.Br Corpus
- BERT
- BERTimbau
- BERTopic
- Hugging Face Transformers
- Scikit-learn
