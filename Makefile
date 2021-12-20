full: clean build-start

start: environment
	@docker-compose run --rm --name chatbot-app app

build-start: environment
	@docker-compose build
	@docker-compose run --rm --name chatbot-app app

clean:
	@docker-compose down
	@rm -rf environment/

environment:
	@mkdir environment 2> /dev/null || :

.PHONY: full start build-start clean environment