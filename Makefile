full: clean build-start

start: environment
	@docker-compose run --rm --name chatbot-app app
#	@docker-compose down --remove-orphans

build-start: environment
	@docker-compose build
	@docker-compose run --rm --name chatbot-app app
	@docker-compose down --remove-orphans

clean:
	@docker-compose down
	@rm -rf environment/

environment:
	@mkdir environment

.PHONY: full start build-start clean