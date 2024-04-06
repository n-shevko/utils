## How to use 'script cleaner'

There are 2 models that app can use: gpt-4 (0613), claude 3 (opus-20240229)

There are 2 algorithms which define how the app feeds text to the models:
1. Cheap algorithm
2. Expensive algorithm (not implemented for gpt-4 but possible if needed)


## Cheap algorithm

For example we have the following prompt:
```
{chunk}

Convert the text above to standard English.
```

Original text is split into N chunks. 
Each chunk replaces {chunk} in the prompt and is sent to the model.

So if the original text is "abc efg" and chunk size is 3 letters then we will have 2 short prompts:

```
abc

Convert the text above to standard English.
```

```
efg

Convert the text above to standard English.
```

These prompts won't consume a lot of tokens so that why algorithm is cheap. 
Cons of this algorithm that model won't see the whole text so results may be of lower quality.

## Expensive algorithm
For example we have the following prompt:
```
{all_chunks}

Convert the text from chunk number {chunk_number} to standard English. 
Pay attention to other chunks as well to gain more context understanding. Don't add your comments.
```

and original text "abc efg"

Original text is split into N chunks and all these chuks will be inserted into {all_chunks} placeholder.
2 prompts will be generated:
The first prompt
```
[START_CHUNK_0]
abc
[END_CHUNK_0]
[START_CHUNK_1]
efg
[END_CHUNK_1]
Convert the text from chunk number 0 to standard English. 
Pay attention to other chunks as well to gain more context understanding. Don't add your comments.
```

The second prompt
```
[START_CHUNK_0]
abc
[END_CHUNK_0]
[START_CHUNK_1]
efg
[END_CHUNK_1]
Convert the text from chunk number 1 to standard English. 
Pay attention to other chunks as well to gain more context understanding. Don't add your comments.
```

These prompts will consume more tokens so that why it is expensive.

## Why do we need these chunks ?

Both models have a limit for the output (answer) size, approximately 4000 tokens. This means if our original
text is more than 4000 tokens and we ask the model to do something with the text,
its answer can't exceed 4000 tokens and it will definitely shorten our text. So instead,
we ask only about a specific part of the text.