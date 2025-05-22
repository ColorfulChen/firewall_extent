# firewall_extent

TODO：
1. add support to google search video pages.(google_search_page_filter() function in tools/google.py) (priority)
2. add image detection support to google_load.py(priority)
3. 完整的谷歌过滤方案描述(priority)
4. 关键词（正则）
5. 改成flask api服务，提供json这边返回。
6. 性能指标（？）
7. Dockerfile
8. 系统用的是AST插件制作，后期可能会需要改成插件。 https://docs.trafficserver.apache.org/en/9.2.x/developer-guide/plugins/index.en.html ATS官方的插件开发文档

六月中期，五月底之前需要

7. 改成 C/C++ 函数的逻辑
8. add support to to the other website:github*\wikipedia\huggingface\dockerhub\youtube\twitter\facebook\google search\google scholar\google patents (not urgent)
9. replace the test_image with not safe for work content for labeling. (not urgent)
10. change test script(test.py)'s algorithm to output the accuracy for the test function in labeling test image. (not urgent)
11. add llm support to filter long text. (not urgent)
12. add llm vision(claude) to filter nsfw picture. (not urgent)


## Project Overview

This project contains scripts for filtering Google search results and for testing image classification.

## Directory Structure

```
google_load.py
README.md
requirements.txt
test.py
results/
	result-*.txt
test_function/
	aliyun.py
	azure_ocr.py
	blip.py
	example.py
test_image/
	testing_labels.csv
	testing_words/
tools/
	__init__.py
	google.py
	web.py
utils/
	load_google.py
	selenium_wire.py
```

## Key Files and Functionality

### `google_load.py`

This script uses Selenium to open Google, intercept and filter search suggestions and search results based on a predefined list of `filter_words`. It filters both the main search results page and the video search results page. It saves the request and response data to a file in the `responses` directory.

**Key functionalities:**
- Sets up a Selenium WebDriver.
- Intercepts HTTP requests and responses.
- Filters Google search suggestions.
- Filters Google search result pages (main and video).
- Saves intercepted request/response details to a timestamped file.

### `test.py`

This script is a unittest-based test suite for image classification. It loads images from the `test_image/testing_words` directory and uses the `image_detection` function from `test_function.blip` to classify them. The results, including processing time and classification, are saved to a timestamped file in the `results` directory.

**Key functionalities:**
- Uses the `unittest` framework.
- Loads multiple images for testing.
- Calls an image detection function.
- Records the time taken for detection.
- Saves test results to a file.

## How to Run

### `google_load.py`

1.  Ensure you have the necessary dependencies installed (e.g., Selenium, selenium-wire). You might find these in `requirements.txt`.
2.  Run the script from the command line:
    ```bash
    python google_load.py
    ```
3.  The script will open a browser window to Google. After you perform searches and are done, press Enter in the console where the script is running to save the captured responses and close the browser.

### `test.py`

1.  Ensure you have the necessary dependencies installed.
2.  Make sure the test images are present in the `test_image/testing_words` directory.
3.  Run the script from the command line:
    ```bash
    python test.py
    ```
4.  The script will output results to the console and save them in a file within the `results` directory.

## Dependencies

The project relies on several Python libraries. Key dependencies likely include:
- `selenium`
- `selenium-wire`
- Libraries used by `test_function.blip` for image detection.

Refer to `requirements.txt` in the root directory and potentially in `code_to_be_reviewd/google/` for a more complete list of dependencies.

