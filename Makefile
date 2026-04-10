PYTHON3=python3

javbus:
	$(PYTHON3) -m bustag.main download

recommend:
	$(PYTHON3) -m bustag.main recommend

migrate:
	$(PYTHON3) -m bustag.main migrate

migrate-dry-run:
	$(PYTHON3) -m bustag.main migrate --dry-run

migrate-status:
	$(PYTHON3) -m bustag.main migrate-status

migrate-safe:
	bash scripts/migrate.sh

build:
	docker build -t  bustag-app-dev .
	
run:
	docker run --rm -d -v `pwd`/data:/app/data -p 8080:8080 bustag-app-dev 

server:
	$(PYTHON3) bustag/app/index.py

start-env:
	bash scripts/start.sh

publish:
	docker tag bustag-app-dev gxtrobot/bustag-app:latest
	docker push gxtrobot/bustag-app:latest

web-drill-fastapi:
	bash scripts/web_stack_drill.sh fastapi

web-drill-bottle:
	bash scripts/web_stack_drill.sh bottle

web-precheck-fastapi:
	bash scripts/pre_release_web_check.sh fastapi

web-precheck-bottle:
	bash scripts/pre_release_web_check.sh bottle
