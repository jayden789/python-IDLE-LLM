# Design Document


For the code explanation, one of the most important decisions that we made was where to put our code. We wanted other people to easily find the code in the codebase, so we decided to put everything in one file: `llm.py`. This is a big file with the implementation of the LLM model to explain the code, file. The `llm_api.` will make request to the backend so that the server will use prompt for LLM explanation.

Another key decision for this task is that we decided to output the response from the LLM model in another screen besides the IDLE so users will not feel uncomfortable when using this feature. 

For the second screen feature, we decided to make it using Tkinter panel because it is easy to use. Then we decided to disable it when the feature is not being used, and only able it when the feature is being used. We decided to include the request type as the input for the API call because we want to include thetypes (explain code, file summary, and error explanation) to create the prompt for the backend.

For the underlining errors feature, we decided to implement it in the `llm.py` file to take advantage of the already declared and imported objects. Moreover, this is not an existing feature so it makes sense to us that this feature is an extension of our main feature. We hope this feature provides some information to the users of where their errors are in their code so that they can use the main LLM feature to explain and correct the error codes. We have a home-brewed bracket/quote error detection that detects unclosed brackets/quotes. However, this is insufficient so we use a third-party library called “pyflakes” to do further syntax checking. Lastly, we are only able to implement this feature in the editor window. Shell works a bit differently as it does not remember previous variable declarations. This made the feature seems buggy in the shell window so we disable it and only enable this feature in the editor window.

In the backend server, we used API key to interact with the LLM to get the response. When the backend server receives requests from IDE, it get the type of the requests (error_type, code_explain, file_summary), then based on the type, the backend would choose the appropriate prompt and send it to LLM for the associated response. We include two LLM models for more usage (because free tier would have limited requests). Once the server receives LLM’s response, it would send it back to the IDE for rendering in separate panel.
We decided to create backend server so that later on if we want to make this project an open source or publish on Github, then everyone can make API call to backend server without for LLM explanation without having API key (the backend will provide limited use)
### UML Diagram
<img width="794" alt="image" src="https://github.com/user-attachments/assets/163c10b6-1fc9-4ee1-8382-6665baf4a89d" />
<img width="763" alt="image" src="https://github.com/user-attachments/assets/4079a816-7cbd-4d65-8eff-63ae124fe3b4" />


### Alternate approach
An alternate approach we considered was implementing our feature directly inside the existing files, such as `pyshell.py` and `editor.py`, rather than creating new files. This would involve placing all of our logic into files that already contain core functionality for the application. The main advantage of this approach is that it would reduce the number of files in the codebase. With fewer files, the overall structure might appear simpler and more consolidated, which can be helpful in projects where file count is a concern.
However, our team chose not to take this approach because of several significant drawbacks. By placing all logic into large, multipurpose files, we would lose the separation of concerns that is vital for code readability and maintainability. It would be much harder to locate, understand, and debug specific parts of our feature if they were embedded within existing files. Additionally, this approach would make writing and running unit tests more difficult, as the feature would not be as modular or isolated.
Instead, we chose to implement our feature in its own separate files. This decision helped us keep our code organized and modular. With each feature contained in its own file, we could easily identify and navigate our code, which made reviewing pull requests much smoother. It also allowed us to write targeted unit tests and work more independently without interfering with unrelated parts of the codebase. Overall, although the alternate approach could have reduced the number of files, our current method provides better maintainability, testability, and clarity, which are essential in a large and collaborative project.





