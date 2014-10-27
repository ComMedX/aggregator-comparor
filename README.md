aggregator-advisor-example
==========================

Heavily inspired by Miguel's [Flask Mega Tutorial](http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world).

An more-than-a-hello-world exmample application of a chemical database using [rdalchemy](http://github.com/teaguesterling/rdalchemy) to glue between RDKit and SQLAlchemy, with implementations of administrative interfaces that account for chemical data. Additionally, shows how to use functional indexes to index for similarity without creating explicit BFP columns.

**Note:** Many better and best practices for development and deployment of a Flask application are not included in this example in order to focus on the aspects of integrating Flask, RDKit, and SQLAlchemy into a single application.
