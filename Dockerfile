FROM python:3.10 AS compile-image

# Stage 1: Install all needed libraries and venv
RUN apt-get update
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt && pip install ansible
RUN ansible-galaxy collection install cisco.cdo
RUN mkdir /opt/venv/app
RUN cd /opt/venv/app && git clone https://github.com/CiscoDevNet/ansible-cisco-cdo.git
WORKDIR /opt/venv/app/ansible-cisco-cdo

# Final stage
FROM python:3.10 AS build-image
COPY --from=compile-image /opt/venv /opt/venv
COPY --from=compile-image /root/.ansible /root/.ansible
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /opt/venv/app/ansible-cisco-cdo