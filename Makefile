full: clean build-start

start: volume_folders
	@docker-compose run --rm -u $$(id -u):$$(id -g) --name chatbot-app app

build-start: volume_folders
	@docker-compose build
	@docker-compose run --rm -u $$(id -u):$$(id -g) --name chatbot-app app

clean:
	@docker-compose down
	@rm -rf environment/ logs/

volume_folders:
	@mkdir environment logs 2> /dev/null || :

.PHONY: full start build-start clean volume_folders