# Regular Markdown Document

This is a regular markdown document that doesn't contain any clarifai:id markers.

## Purpose

This file is used to test that the vault sync job correctly handles files without any special markers and doesn't attempt to process them.

## Content

- Regular bullet point
- Another bullet point
- A third point without any special markers

## Code Example

```javascript
function greetUser(name) {
    console.log(`Hello, ${name}!`);
}
```

## Conclusion

The vault sync job should skip this file entirely since it contains no clarifai:id blocks.