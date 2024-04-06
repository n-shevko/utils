## How to use 'script cleaner'

There are 2 models that app can use: gpt-4 (0613), claude 3 (opus-20240229)

There are 2 algorithms which define how the app feeds text to the models.

1. Cheap algorithm.

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

2. 
