Based on the conversation above, write a technical specification that has guidance for how to implement what we have discussed.

The output you now give will be used as the requirements guide for AI developers to implement these features. They already know the existing code base, so they will be tasked with the specifics of integrating the changes, and you should not write too much prescriptive code. Be declarative about what the resulting logic and flow should be, be declarative about the models that will be used. But leave nothing important out that we've discussed, while remembering this is an MVP focus.

Start with a high level overview of the changes, briefly summarized in just two or three sentences. Specifics come after.

Following the overview, give a "migration guide" based on your understanding of the current state of the code, and the changes that need to be made to move it into the desired state.

Don't rewrite the code itself here, the other AI developer can handle it as long as your provide quality guidance. But if there are new or changed data models, you may demonstrate them with examples (JSON, xml, or python model).

You will write one long requirements file, but we will tackle the work bit by bit. Consider breaking the changes into iterative milestones.

Format the output as Markdown.

In your instructions, instruct the AI developer to critically evaluate the suggestions you make: the real code base might have slightly different names or niches, and the AI developer will need to intelligently adapt and integrate your suggestions without
blindly following everything to the letter. Write a reminder in your instructions to this effect.

There are already rules and code standards in place, which are accessible to the AI developer, about linting, typechecking, running tests, and how to write tests in place: add a reminder at the very end to follow these rules.

If there are any important caveats, gotchas, edge cases, or considerations that we have talked about in our conversation so far,
make sure to note them in your instructions.

Provide brief explanation of the reasoning behind important changes, so that the AI developer better understands the intent behind
the changes.

If you have any questions about these instructions, it's important you ask now. If you do not have questions, you may begin writing them, please.
