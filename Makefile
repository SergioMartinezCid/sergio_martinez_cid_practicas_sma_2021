full: clean build-start

start:
	docker-compose up --remove-orphans --abort-on-container-exit

build-start:
	docker-compose up --build --remove-orphans --abort-on-container-exit

clean:
	docker-compose down

.PHONY: full start build-start clean