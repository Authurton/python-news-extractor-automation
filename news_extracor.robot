*** Settings ***
Library           SeleniumLibrary
Library           DateTime

*** Variables ***
${SEARCH_PHRASE}       climate change
${NEWS_CATEGORY}       climate
${MONTHS_TO_EXTRACT}   3
${BASE_URL}            https://www.latimes.com/

*** Test Cases ***
Test News Extraction
    Open Browser    ${BASE_URL}    chrome
    Set Window Size    1920    1080
    Extract News
    Close Browser

*** Keywords ***
Extract News
    [Arguments]    ${search_phrase}=${SEARCH_PHRASE}    ${news_category}=${NEWS_CATEGORY}    ${months_to_extract}=${MONTHS_TO_EXTRACT}
    [Documentation]    Extract news articles from the website
    [Tags]    news
    Open Browser    ${BASE_URL}    chrome
    Set Window Size    1920    1080
    ${extractor} =    Evaluate    NewsExtractor($search_phrase, $news_category, $months_to_extract)
    ${news_articles} =    Call Method    ${extractor}    extract_news
    Log Many    ${news_articles}
    Should Not Be Empty    ${news_articles}
    Close All Browsers
