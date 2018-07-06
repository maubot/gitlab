FROM golang:1-alpine AS builder

RUN apk add --no-cache git ca-certificates
RUN wget -qO /usr/local/bin/dep https://github.com/golang/dep/releases/download/v0.4.1/dep-linux-amd64
RUN chmod +x /usr/local/bin/dep

COPY Gopkg.lock Gopkg.toml /go/src/maubot.xyz/gitlab/
WORKDIR /go/src/maubot.xyz/gitlab
RUN dep ensure -vendor-only

COPY . /go/src/maubot.xyz/gitlab
RUN CGO_ENABLED=0 go build -o /usr/bin/maulabbot


FROM scratch

COPY --from=builder /usr/bin/maulabbot /usr/bin/maulabbot
COPY --from=builder /etc/ssl/certs/ /etc/ssl/certs

CMD ["/usr/bin/maulabbot", "-c", "/etc/maulabbot/config.json", "-t", "/etc/maulabbot/tokens.json"]
