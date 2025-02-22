"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
import datetime
from api.models import db, User, Animal, Shelter
from api.utils import generate_sitemap, APIException
from werkzeug.security import generate_password_hash, check_password_hash


import cloudinary
import cloudinary.uploader
import cloudinary.api


api = Blueprint('api', __name__)



# ...................LOGIN, REGISTERADOPTER, REGISTERSHELTER, REGISTERANIMAL.................

@api.route('/login', methods=['POST'])
def login():
    
    email, password, type = request.json.get('email', None), request.json.get('password', None), request.json.get('type', None)

    if not (email and password):
        return jsonify({'message': 'Data not provided'}), 400

    # traer de mi base de datos un usuario por su email
    user = None
    if type:
        # shelter
        user = Shelter.query.filter_by(email=email).one_or_none()
    else:
        # adopter
        user = User.query.filter_by(email=email).one_or_none()
       

    if not user:
        return jsonify({'message': 'Email is not valid'}), 404

    # comprobar si la contraseña es correcta
    if not check_password_hash(user.password, password):
        return jsonify({'message': 'Your pass doesn"t match'}), 500

    token = create_access_token(identity=user.id, expires_delta = datetime.timedelta(minutes=60))

    
    return jsonify({'token':token, 'type': type, 'user':user.serialize()}), 200


@api.route('/signupadopter', methods=["POST"])
def signUpAdopter():

    name = request.json.get('name', None)
    surname = request.json.get('surname', None)
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    passwordrepeat = request.json.get('passwordrepeat', None)
    age = request.json.get('age', None)
    city = request.json.get('city', None)
    address = request.json.get('address', None)
    

    if not (name and surname and email and password and age and city and address and passwordrepeat):
        return jsonify({'message': 'Data not provided'}), 400

    hash_password = generate_password_hash(password)
    user = User(name=name, surname=surname, email=email, password=hash_password, age=age, city=city, address=address)
    try:

        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=user.id, expires_delta = datetime.timedelta(minutes=60))
        return jsonify({'token': token}), 201

    except Exception as err:
        return jsonify({'message': str(err)}), 500

@api.route('/signupshelter', methods=["POST"])
def signUpShelter():

    name = request.json.get('name', None)
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    passwordrepeat = request.json.get('passwordrepeat', None)
    city = request.json.get('city', None)
    address = request.json.get('address', None)
    tlf = request.json.get('tlf', None)

    if not (name and email and password and passwordrepeat and city and address):
        return jsonify({'message': 'Data not provided'}), 400
    
    hash_password = generate_password_hash(password)
    shelter = Shelter(name=name, email=email, password=hash_password, city=city, address=address, tlf=tlf)
    try:

        db.session.add(shelter)
        db.session.commit()
        token = create_access_token(identity=shelter.id, expires_delta = datetime.timedelta(minutes=60))
        return jsonify({'token': token}), 201

    except Exception as err:
        return jsonify({'message': str(err)}), 500

@api.route('/registeranimal', methods=["POST"])
@jwt_required()
def registerAnimal():

    cloudinary.config(
        cloud_name = 'dqhlna24b',
        api_key='785699686264573',
        api_secret='IEigIKmf9mWFvQG9jk87DYO39eo'
    )

    file_to_upload = request.files.get('file')
    
    id = get_jwt_identity()
    shelter = Shelter.query.get(id)
    name = request.form.get('name', None)
    species = request.form.get('species', None)
    gender = request.form.get('gender', None)
    race = request.form.get('race', None)
    size = request.form.get('size', None)
    age = request.form.get('age', None)
    short_description = request.form.get('short_description', None)
    description = request.form.get('description', None)
    
    if not (name and species and gender and race and size and age and short_description and description):
        
        return jsonify({'message': 'Data not provided'}), 400
    
    animal = Animal(name=name, species=species, gender=gender, race=race, size=size, age=age, short_description=short_description, description=description, shelter_id=shelter.id)
    try:

        db.session.add(animal)
        shelter.animals.append(animal)
        db.session.commit()
        
        if file_to_upload:
            upload_result = cloudinary.uploader.upload(file_to_upload)      
            if upload_result:
                imageprofile = upload_result.get('secure_url')
                animal.image = imageprofile
                if animal.image:
                    final = animal.image
                    
                try:
                    db.session.commit()
                    return jsonify({'results':"guardado hecho perfecto"}), 200

                except Exception as err:
                    print(str(err))
                    return jsonify({'message': str(err)}), 500

            return jsonify({'results':animal.serialize()}), 200

    except Exception as err:
        return jsonify({'message': str(err)}), 500

# .........................OBTENER (GET) INFO DE LA API.....................................
@api.route('/allanimals', methods=['GET'])
def get_all_dogs():
    animals = Animal.query.all()
    
    return jsonify({'results': list(map(lambda animal: animal.serialize(), animals))}),200

@api.route('/allshelters', methods=['GET'])
def get_all_shelters():
    shelters = Shelter.query.all()
    return jsonify({'results': list(map(lambda shelter: shelter.serialize(), shelters))}),200


@api.route('/detailanimal/<int:id>', methods=['GET'])
def get_animal_by_id(id):
    animal = Animal.query.get(id)
    return jsonify({'results': animal.serialize()}),200

@api.route('/shelterinfoforviewadopter/<int:id>', methods=['GET'])
def get_shelter_profile_for_view_adopter(id):
    shelter = Shelter.query.get(id)
    return jsonify({'results': shelter.serialize()}),200

@api.route('/animalsforviewadopter/<int:id>', methods=['GET'])
def get_animals_in_shelter_for_view_adopter(id):
    animals = Animal.query.filter(Animal.shelter_id == id)
    
    return ({'results':[animal.serialize() for animal in animals]})

@api.route('/adopterinfo', methods=['GET'])
@jwt_required()
def get_adopter_info():
    id = get_jwt_identity()

    adopter = User.query.get(id)
    return jsonify({'results': adopter.serialize()}),200

@api.route('/shelterinfo', methods=['GET'])
@jwt_required()
def get_shelter_info():
    id = get_jwt_identity()

    shelter = Shelter.query.get(id)

    return jsonify({'results': shelter.serialize()}),200

# un GET de profile/animal prtegida por token
# 
@api.route('/profile/animal', methods=['GET'])
@jwt_required()
def animals_in_my_shelter():
    
    id = get_jwt_identity()
    animals = Animal.query.filter(Animal.shelter_id == id)
    
    return ({'results':[animal.serialize() for animal in animals]})





# ....................EDITAR INFORMACION EN DETERMINADOS CAMBIOS DE LAS BD.........................................

@api.route('/editinfoadpoter', methods=['PUT'])
@jwt_required()
def edit_info_adopter():
    id = get_jwt_identity()
    adopterId = User.query.get(id)
    
    name = request.json.get('name', None)
    surname = request.json.get('surname', None)
    email = request.json.get('email', None)
    password = request.json.get('password', None)
    age = request.json.get('age', None)
    city = request.json.get('city', None)
    address = request.json.get('address', None)
    
    if password != None:
        hash_password = generate_password_hash(password)   

    if  (name or surname or email or hash_password or age or city or address ):
            if name != None:
                adopterId.name = name
            if surname != None:  
                adopterId.surname = surname
            if email != None:
                adopterId.email = email
            if password != None:
                adopterId.password = hash_password
            if age !=None:
                adopterId.age = age
            if city != None:
                adopterId.city = city
            if address != None:
                adopterId.address = address
            
            db.session.commit()
            
            return jsonify({'results': adopterId.serialize()}),201

@api.route('/editinfoshelter', methods=['PUT'])
@jwt_required()
def edit_info_shelter():
    id = get_jwt_identity()
    adopterId = Shelter.query.get(id)
    
    name = request.json.get('name', None)
    surname = request.json.get('surname', None)
    email = request.json.get('email', None)
    age = request.json.get('age', None)
    city = request.json.get('city', None)
    address = request.json.get('address', None)
    password = request.json.get('password', None)
    
    
    hash_password = generate_password_hash(password)   

    if (name or surname or email or age or city or address or hash_password):
        if name != None:
            adopterId.name = name
        if surname != None:  
            adopterId.surname = surname
        if email != None:
            adopterId.email = email
        if age !=None:
            adopterId.age = age
        if city != None:
            adopterId.city = city
        if address != None:
            adopterId.address = address
        if hash_password != None:
            adopterId.password = hash_password
                
            db.session.commit()
                
            return jsonify({'results': adopterId.serialize()}),201
        
     
@api.route('/editinfoanimal/<int:id>', methods=['PUT'])
@jwt_required()
def edit_info_animal(id):
    
    animal = Animal.query.get(id)
    
    name = request.json.get('name', None)
    species = request.json.get('species', None)
    race = request.json.get('race', None)
    gender = request.json.get('gender', None)
    size = request.json.get('size', None)
    age = request.json.get('age', None)
    description = request.json.get('description', None)
    short_description = request.json.get('short_description', None)
    
  

    if  (name or species or gender or race or size or age or description or short_description ):
            if name != None:
                animal.name = name
            if species != None:  
                animal.species = species
            if gender != None:
                animal.gender = gender
            if race != None:
                animal.race = race
            if size !=None:
                animal.size = size
            if age !=None:
                animal.age = age
            if description != None:
                animal.description = description
            if short_description != None:
                animal.short_description = short_description
            
            db.session.commit()
            
            return jsonify({'results': animal.serialize()}),201


@api.route('/editprofilephotoshelter', methods=['PUT'])
@jwt_required()
def edit_profile_photo_shelter():
    
    id = get_jwt_identity()
    shelterId = Shelter.query.get(id)

    cloudinary.config(
        cloud_name = 'dqhlna24b',
        api_key='785699686264573',
        api_secret='IEigIKmf9mWFvQG9jk87DYO39eo'
    )

    file_to_upload = request.files.get('file')
    
    upload_result = None

    if file_to_upload:
        upload_result = cloudinary.uploader.upload(file_to_upload)      
        if upload_result:
            imageprofile = upload_result.get('secure_url')
            shelterId.image = imageprofile
            if shelterId.image:
                final = shelterId.image
                
            try:
                
                db.session.commit()
                return jsonify({'results':"guardado hecho perfecto"}), 200

            except Exception as err:
                print(str(err))
                return jsonify({'message': str(err)}), 500

@api.route('/editprofilephotoadopter', methods=['PUT'])
@jwt_required()
def edit_profile_photo_adopter():
    
    id = get_jwt_identity()
    adopterId = User.query.get(id)

    cloudinary.config(
        cloud_name = 'dqhlna24b',
        api_key='785699686264573',
        api_secret='IEigIKmf9mWFvQG9jk87DYO39eo'
    )

    file_to_upload = request.files.get('file')
    
    upload_result = None

    if file_to_upload:
        upload_result = cloudinary.uploader.upload(file_to_upload)      
        if upload_result:
            imageprofile = upload_result.get('secure_url')
            adopterId.image = imageprofile
            if adopterId.image:
                final = adopterId.image
                
            try:
                
                db.session.commit()
                return jsonify({'results':"guardado hecho perfecto"}), 200

            except Exception as err:
                print(str(err))
                return jsonify({'message': str(err)}), 500


@api.route('/editanimal/<int:id>', methods=['PUT'])
def edit_animal_photo(id):
    
    
    animalId = Animal.query.get(id)

    cloudinary.config(
        cloud_name = 'dqhlna24b',
        api_key='785699686264573',
        api_secret='IEigIKmf9mWFvQG9jk87DYO39eo'
    )

    file_to_upload = request.files.get('file')
    
    upload_result = None

    if file_to_upload:
        upload_result = cloudinary.uploader.upload(file_to_upload)      
        if upload_result:
            imageprofile = upload_result.get('secure_url')
            animalId.image = imageprofile
            if animalId.image:
                final = animalId.image
                
            try:
                
                db.session.commit()
                return jsonify({'results':"guardado hecho perfecto"}), 200

            except Exception as err:
                print(str(err))
                return jsonify({'message': str(err)}), 500


# ...........................DELETE ANIMALSS.......................................................

@api.route("/deleteanimal/<int:id>", methods=["DELETE"])
def delete_animal(id):
    animal = Animal.query.get(id)
    db.session.delete(animal)
    db.session.commit()

    return jsonify({'perfect':'Animal borrado con existo'}), 200


# ...................RUTAS RELACIONADAS CON FAVORITOS MANYTOMANY...................................

@api.route('/favanimal/<int:animal_id>', methods=['POST'])
@jwt_required()
def save_fav_animal(animal_id):

    id = get_jwt_identity()
    adopter = User.query.get(id)
    
    animal = Animal.query.get(animal_id)
    if animal not in adopter.animalsfav:
        adopter.animalsfav.append(animal)
        db.session.add(animal)
        db.session.commit()
        return jsonify({'response': True}),200
    else:
        adopter.animalsfav.remove(animal)
        db.session.commit()
        return jsonify({'response': False}),200





@api.route('/user/favlist', methods=['GET'])
@jwt_required()
def get_fav_list():
    id = get_jwt_identity()
    userfavs = User.query.get(id)

    if userfavs:
        user_favorites = userfavs.animalsfav
        all_favorites = [favorite.serialize() for favorite in user_favorites] # serializame por cada favorito, en user_favorites
        return jsonify(all_favorites), 200
   
    return jsonify({'error': 'No favourite animals'}),404


# ............................FilterBar............................................................
@api.route('/filteranimals', methods=['POST'])
def filter_animals():

   

    species = request.json.get('species', None)
    gender = request.json.get('gender', None)
    size = request.json.get('size', None)
    age = request.json.get('age', None)
    city = request.json.get('city', None)
    

    

    queries = []
    if species:
        queries.append(Animal.species == species)
    if gender:
        queries.append(Animal.gender == gender)
    if size:
        queries.append(Animal.size == size)
    if age:
        min_age = 0
        if age == "cachorro":
            age = 1
        elif age == "adulto":
            age = 7
            min_age = 1
        elif age == "mayor":
            age = 1000
            min_age = 7
        queries.append(Animal.age <= age)
        queries.append(Animal.age > min_age)
    
    animals = Animal.query.filter(*queries)

    animal_by_city = []
    if city:
        for animal in animals:
            if Shelter.query.get(animal.shelter_id).city == city:
                animal_by_city.append(animal)
        return jsonify({'results': list(map(lambda animal: animal.serialize(), animal_by_city))}), 200

    
    return jsonify({'results': list(map(lambda animal: animal.serialize(), animals))}), 200


# .....................VALIDACION DE TOKEN PARA ADOPTER AND SHELTER...............................


# Authorization: Bearer <token> => si no viene 401
@api.route('/nouser', methods=['GET'])
@jwt_required()
def validateNoToken():

    userId = get_jwt_identity()
    user = User.query.get(userId)
    if user:
        return jsonify({"validate": True})
    else:
        return jsonify({"validate": False})




@api.route('/user', methods=['GET'])
@jwt_required()
def validateToken():

    userId = get_jwt_identity()
    user = User.query.get(userId)
    if user:
        return jsonify({"validate": True})
    else:
        return jsonify({"validate": False})

@api.route('/shelter', methods=['GET'])
@jwt_required()
def getShelterInfo():

    shelterId = get_jwt_identity()
    shelter = Shelter.query.get(shelterId)
    if shelter:
        return jsonify({"validate": True})
    else:
        return jsonify({"validate": False})



# .......................Rutas de control para ver la info en la API...............................


@api.route('/allusers', methods=['GET'])
def get_all_users():
    users = User.query.all()
    return jsonify({'results': list(map(lambda user: user.serialize(), users))}),200

