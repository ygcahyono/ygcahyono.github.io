---
layout: post
title: "Launch the first DBT Project with Snowflake"
date: 2025-09-01 13:45:00
categories: Analytics Tools
tags: [ETL, Analytics, Tools]
---

This post is to help someone who are trying to understand the practical implementation of DBT (like me). On top of that in this guide, I will specifically use Snowflake plugin. Since, couple weeks back, I finished "Hands On Essentials" on Snowflake. So I thought it was pretty low hanging fruit to learn basic of dbt afterwards.

Without further ado let's start: 

1. Installation of dbt-core and dbt-snowflake

    - create a private conda env for dbt

    ``` conda create -n dbt python=3.9 ```
    ``` conda activate dbt ```
    ``` pip install dbt-core dbt-snowflake ```

https://docs.getdbt.com/docs/core/pip-install#pip-install-dbt

2. Create a local folder for the dbt init backbone
3. Create a profiles.yml files to build a connection from local to snowflake cloud
    - get the template for snowflake connection set up from the dbt website https://docs.getdbt.com/docs/core/connect-data-platform/snowflake-setup
    - Fill the detail credentials
4. Everything is set up for initial tests
    - Check the connection via dbt debug
    - dbt run
    - changes should be available online
5. (extras) Create a github folder



This platform is helping me to understand the common tools that analytics poeple use right now, especially here in the UK (eg. Snowflake and DBT). Since my previous employer using everything in-house. We did not have really aware what kind of tools that popularly used today.

I want to say thanks to Kahan Data Solutions, since most of the tutorial provided by this guy 4 years ago. Even though I found it quite challenging since the UI already changed a lot for four years and cannot find exact pages that were referred to in the video. This post hopefully become a good refreshment for everyone.