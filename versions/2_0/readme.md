# Duck 2.0
Stronger, faster, lighter, more durable.
it talks. It walks. It quacks.

## Goal

hack every piece together into isolated services in python.
A lot of the stuff I want to do can also be done in node.js
but the documentation for it is much more sparse, and the error handling in many cases isn't there.
So it's all being written in python first, then translated into js.
Most the APIs are the same in JS as they are in python, but the error handling isn't there.
Much of the python is just a wrapper around some c/c++, rust, or some other compiled/lower level/optimized language/runtime.

It seemed like openvino would support the NPU in js.
but it would fail silently.

The same code in python wouldn't work, but i figured out why. The errors were there.
If that works, something similar might work in JS, if I can work around not having any errors.

Even if it doesn't right off the bat, doesn't matter.

as much as we can is going to get javascriptized.
js is faster.

Just people write documentation for python.
people do research  in python.

The community who builds this stuff writes python.
So the guides are written in python.

We'll see.

i'm pretty committed to getting it to work in JS
Where I have a good lisp.

If tht fails, there is always hy.
I get enough of the python in hy, and my AI can figure it out.

it's all just gonna be flask apps for now.
I can make it better.
but I just need seperate processes for now.

I need concurrency.

We're here because I got each individual piece to work in isolation.
now it needs to be cleaned up and seperated.
modularized.

## Services
- stt
- tts
- llm
- discord_speech
- webcrawler
- discord_message_indexer
- file_indexer
- UI
