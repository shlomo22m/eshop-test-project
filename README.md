# Rafael automation bootcamp final project
## Introduction
Each student should write a set of automation test cases in Python.
The test cases will be based on collection of micro services that will function as a “Unit Under Test” – “EshopOnline” website.
Every student will be assigned one or more micro services to implement automation tests for.

The project will include the following:
1.	Python code committed and pushed to a personal GitHub repository (for each student)
2.	Presentation in power point / google slides explaining the project

The code of the project should include:
1.	Usage of various python components learned in the course
2.	Usage of a testing infrastructure (pytest)
3.	Test coverage of each micro service assigned to the student.

## Project preparation and workflow
1.	Download and install the following on your machine: Docker desktop,  Postman, Python, Pycharm CE, GitHub Desktop
2.	Clone this repository to your machine
3.	Create a new branch with your full name as the name of the branch and check out the branch locally
4.	Run command “pip install -r requirements.txt” from the repository directory
5. Write your tests in the "tests" package. You may use the utility modules in the "utils" package.
5.	Run your tests using "pytest" command in command line and make sure that a report is created.
6.	Commit and push the code to GitHub on your branch. 

## Coding principles
1.	You are required to implement a fully working automation system for the EshopOnline system
2.	Each method should have a docstring explaining what the method does - https://www.programiz.com/python-programming/docstrings
3.	The code should be well structured and well documented
4.	Every use case in the code should be tested before submitting the code
5.	Every exception should be raised correctly with a proper message
6.	Add a requirements.txt file with any additional modules required – optional
7.	Each student will work on his/her GitHub repository
8.	All code should be merged to master at the final submission

## Project presentation
1.	Presentation will be in Power point / Google slides explaining the process for building the project
2.	The slides should show also the QA process and test cases covered in the project
3.	The slides should include the report HTML of the pytest results
4.	One of the slides should include a topic of your choice that you learned during the project
5.	The presentation should also include a live demo of one or more tests
6.	Finally, the code will be presented from GitHub for review
 
## Unit under test description
The UUT for the project is called “EshopOnline”. It’s an online shop website which includes client applications, backend micro services, API Gateways, DBs and an Event bus to communicate between the micro services.
The whole system is launched as a docker containers on your local machine.
Each micro service is running independently as listed in the diagram below:

<img src="https://github.com/dotnet-architecture/eShopOnContainers/raw/dev/img/eShopOnContainers-architecture.png" alt="Eshop containers architecture">

## List of services:
* Basket API – Handles shopping basket
* Catalog API – Handles the store catalog
* Identity API – Handles shop customers
* Payment API – Handles customer payments
* Ordering API – Handles orders after purchases
* Event bus – Handles communications between services
* Web status – Shows the status of each service
* Web/mobile clients – Used for system review / manual testing
