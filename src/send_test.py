import pika
from message import GenerateReportMessageRequest, EmployeeMessage

RABBIT_MQ = 'ssh.grassi.dev'
INCOMING_MSG_QUEUE = 'incoming-msgs'
OUTGOING_MSG_QUEUE = 'outgoing-msgs'

print("[info] :: connecting to RabbitMQ for handling messages...")

connection = pika.BlockingConnection(pika.ConnectionParameters(RABBIT_MQ))
channel = connection.channel()

# Declare an incoming and outgoing for queues
channel.queue_declare(INCOMING_MSG_QUEUE)

msg = GenerateReportMessageRequest('Alessandro Grassi', 'John Doe', 'it', 'en', [
    EmployeeMessage(EmployeeMessage.Kind.TEXT, "Il sottoscritto impiegato ha riportato un incidente a casa con il suo dinosauro domestico. Purtroppo, durante una passeggiata quotidiana, il dinosauro si è agitato improvvisamente, causando danni significativi al bagno dell'impiegato. L'incidente ha causato la rottura del lavandino, della doccia e del water. Inoltre, le pareti e il pavimento del bagno sono stati gravemente danneggiati. L'impiegato ha quindi deciso di procedere con il rinnovo del bagno per garantire la sicurezza e il comfort della sua famiglia. L'impiegato ha tempestivamente informato il suo responsabile dell'incidente e ha presentato una richiesta di spese straordinarie per la ristrutturazione del bagno. La richiesta è stata valutata e approvata in linea con le politiche aziendali. Il progetto di rinnovo del bagno è stato affidato a un professionista qualificato, che ha completato i lavori in tempo e con un budget rispettoso. Il nuovo bagno è ora completamente funzionante e presenta miglioramenti significativi rispetto alla versione precedente. L'impiegato si è impegnato attivamente nel processo di rinnovo del bagno, fornendo supporto al professionista e garantendo la continuità del lavoro durante il periodo di ristrutturazione. Ha inoltre adottato misure preventive per evitare ulteriori incidenti domestici, come ad esempio l'implementazione di un'area sicura per il dinosauro domestico.In sintesi, l'impiegato ha gestito l'incidente con professionalità e tempestività, adottando misure efficaci per garantire la sicurezza e il comfort della sua famiglia. Il suo contributo al processo di rinnovo del bagno è stato prezioso e apprezzato."),
    EmployeeMessage(EmployeeMessage.Kind.IMAGE, "https://pngimg.com/d/dinosaur_PNG16611.png"),
    EmployeeMessage(EmployeeMessage.Kind.IMAGE, "https://www.thespruce.com/thmb/J53yaSLGsDzkOOTYiXuP52oMJ8I=/2048x0/filters:no_upscale():max_bytes(150000):strip_icc()/modern-bathroom-design-ideas-4129371-hero-723611e159bb4a518fc4253b9175eba8.jpg")
])

channel.basic_publish(exchange='', routing_key=INCOMING_MSG_QUEUE, body=msg.to_json())

print("[info] :: start main message loop...")
channel.start_consuming()